#!/usr/bin/env python3
import sys
import time
from pyspark.sql import SparkSession


def game_of_life(spark, N, generations):
    sc = spark.sparkContext
    # configuração inicial: “veleiro” no canto superior esquerdo
    initial_alive = [(1, 2), (2, 3), (3, 1), (3, 2), (3, 3)]
    alive_rdd = sc.parallelize(initial_alive).persist()

    for _ in range(generations):
        # coletar e broadcastar o conjunto atual de vivos
        current_alive = set(alive_rdd.collect())
        alive_bc = sc.broadcast(current_alive)

        # cada célula viva gera +1 para cada vizinho
        neighbor_counts = (
            alive_rdd.flatMap(
                lambda cell: [
                    ((cell[0] + di, cell[1] + dj), 1)
                    for di in (-1, 0, 1)
                    for dj in (-1, 0, 1)
                    if not (di == 0 and dj == 0)
                ]
            )
            # manter dentro do tabuleiro [1..N]×[1..N]
            .filter(lambda x: 1 <= x[0][0] <= N and 1 <= x[0][1] <= N).reduceByKey(
                lambda a, b: a + b
            )
        )

        # aplicar regras de Conway
        alive_rdd = neighbor_counts.filter(
            lambda cell_cnt: (
                cell_cnt[1] == 3 or (cell_cnt[1] == 2 and cell_cnt[0] in alive_bc.value)
            )
        ).map(lambda cell_cnt: cell_cnt[0])

    return alive_rdd.collect()


def main():
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <powmin> <powmax>")
        sys.exit(1)

    powmin, powmax = map(int, sys.argv[1:3])
    spark = SparkSession.builder.appName("GameOfLifeSpark").getOrCreate()

    for p in range(powmin, powmax + 1):
        N = 1 << p
        generations = 2 * (N - 3)

        t0 = time.time()
        # (aqui só inicializa; no Spark, a parallelize já carrega os dados)
        t1 = time.time()

        # executa as gerações
        _ = game_of_life(spark, N, generations)
        t2 = time.time()

        print(
            f"**RESULTADO SPARK** tam={N}; init={t1-t0:.3f}, comp={t2-t1:.3f}, tot={t2-t0:.3f}"
        )

    spark.stop()


if __name__ == "__main__":
    main()
