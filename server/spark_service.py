import socket, threading, time
from pyspark.sql import SparkSession


def game_of_life(spark, N, generations):
    sc = spark.sparkContext
    initial = [(1, 2), (2, 3), (3, 1), (3, 2), (3, 3)]
    alive = sc.parallelize(initial).persist()
    for _ in range(generations):
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
            ).map(lambda cc: cc[0])
        ).persist()
    return alive.collect()


def handle_client(conn, spark):
    try:
        data = conn.recv(1024).decode().strip()
        pmin, pmax = map(int, data.split(","))
        out = []
        for p in range(pmin, pmax + 1):
            N, gens = 1 << p, 2 * ((1 << p) - 3)
            t0 = time.time()
            _ = game_of_life(spark, N, gens)
            t1 = time.time()
            out.append(f"tam={N}; comp={t1-t0:.3f}s")
        conn.sendall(("\n".join(out) + "\n").encode())
    finally:
        conn.close()


if __name__ == "__main__":
    spark = (
        SparkSession.builder.appName("GameOfLifeService")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    HOST, PORT = "0.0.0.0", 65432
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen()
    print(f"[SparkService] pronto em {HOST}:{PORT}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, spark), daemon=True).start()
