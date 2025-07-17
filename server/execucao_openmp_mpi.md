# Game of Life Distribuído (MPI+OpenMP + Spark)

Este repositório reúne uma prova de conceito para executar o **Game of Life** em dois ambientes distribuídos:

1. **MPI + OpenMP** em C
2. **Apache Spark** em Python, com contexto “sempre quente”

Tudo orquestrado por um servidor TCP (`socket_server.py`), que escolhe entre MPI ou Spark conforme o comando do cliente. Por hora rodamos **localmente**; futuramente migraremos para um cluster Kubernetes com 3 nós.

---

## Componentes

### 1. `jogodavida_openmp_mpi.c`

- Implementação em C usando **MPI** (para distribuir linhas entre processos) e **OpenMP** (para paralelizar internamente cada fatia).
- Mede três tempos por dimensão N=2^p:
  - **init**: inicialização e broadcast do tabuleiro
  - **comp**: iterações de Conway
  - **tot**: total (init + comp)
- Saída no terminal:

### 2. `jogodavida_spark_service.py`

- Serviço Python que inicia **uma única** SparkSession (`local[*]`) e mantém executors vivos.
- Escuta na porta **65432** via socket TCP.
- Recebe `<powmin>,<powmax>`, executa o algoritmo e retorna, para cada p:

### 4) Compilação e Execução Local (detalhada)

Para facilitar testes e estudos antes de migrar para Kubernetes, seguem os comandos passo a passo.

#### 4.1) Compilar a versão MPI+OpenMP

mpicc -O3 -march=native -fopenmp jogodavida_mpi_openmp.c -o jogodavida_openmp_mpi

#### 4.2) Iniciar o SparkService

chmod +x jogodavida_spark_service.py
./jogodavida_spark_service.py
deve exibir:
[SparkService] pronto em 0.0.0.0:65432

#### 4.3) Iniciar o SocketServer

python3 socket_server.py

deve exibir:

[SocketServer] ouvindo em 0.0.0.0:65431

---

### 5) Testes

#### 5.1) MPI + OpenMP

echo "mpi,3,5" | nc localhost 65431

Saída esperada:
**RESULTADO CORRETO**
tam=8; tempos: init=0.012, comp=0.098, tot=0.110
**RESULTADO CORRETO**
tam=16; tempos: init=0.020, comp=0.275, tot=0.295

#### 5.2) Spark

echo "spark,3,5" | nc localhost 65431

Saída esperada:
**RESULTADO SPARK**
tam=8; tempos: init=0.005, comp=0.580, tot=0.585
**RESULTADO SPARK**
tam=16; tempos: init=0.010, comp=3.100, tot=3.110
