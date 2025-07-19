#!/usr/bin/env python3
import socket
import threading
import time
from pyspark.sql import SparkSession


def handle_client(conn, spark):
    try:
        # recebe pmin,pmax do cliente
        data = conn.recv(1024).decode().strip()
        pmin, pmax = map(int, data.split(","))

        lines = []
        for p in range(pmin, pmax + 1):
            N = 1 << p
            gens = 2 * (N - 3)
            sc = spark.sparkContext

            # 1) init: paraleliza e cacheia o estado inicial
            t0 = time.time()
            initial = [(1, 2), (2, 3), (3, 1), (3, 2), (3, 3)]
            alive = sc.parallelize(initial).persist()
            t1 = time.time()

            # 2) comp: executa o loop de gerações
            for _ in range(gens):
                nbrs = (
                    alive.flatMap(
                        lambda c: [
                            ((c[0] + di, c[1] + dj), 1)
                            for di in (-1, 0, 1)
                            for dj in (-1, 0, 1)
                            if not (di == 0 and dj == 0)
                        ]
                    )
                    .filter(lambda x: 1 <= x[0][0] <= N and 1 <= x[0][1] <= N)
                    .reduceByKey(lambda a, b: a + b)
                )
                current = set(alive.collect())
                bc = sc.broadcast(current)
                alive = (
                    nbrs.filter(
                        lambda cc: cc[1] == 3 or (cc[1] == 2 and cc[0] in bc.value)
                    )
                    .map(lambda cc: cc[0])
                    .persist()
                )
            t2 = time.time()

            # 3) monta saída igual ao MPI+OpenMP
            lines.append("**RESULTADO SPARK**")
            lines.append(
                f"tam={N}; tempos: init={t1-t0:.3f}, comp={t2-t1:.3f}, tot={t2-t0:.3f}"
            )

        # envia tudo de volta ao cliente
        conn.sendall(("\n".join(lines) + "\n").encode())

    finally:
        conn.close()


if __name__ == "__main__":
    # cria SparkSession uma única vez
    spark = (
        SparkSession.builder.appName("GameOfLifeService")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    # configura socket
    HOST, PORT = "0.0.0.0", 65432
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen()
    print(f"[SparkService] pronto em {HOST}:{PORT}")

    # aceita conexões e despacha threads
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, spark), daemon=True).start()
