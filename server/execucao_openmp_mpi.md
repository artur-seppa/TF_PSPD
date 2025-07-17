# Execução

## Compilacao Local

mpicc -o jogodavida_openmp_mpi jogodavida_openmp_mpi.c -fopenmp

## testando servidor que chama o openmp service

Agora com o jogodavida_openmp_mpi.c

## Compilação Server

mpicc -O3 -march=native -o jogodavida_openmp_mpi jogodavida_openmp_mpi.c -fopenmp

## execute o servidor

python3 socket_server.py

## Teste com cliente (em outro terminal):

echo "3,5" | nc localhost 65432

# Ou

python3 -c "import socket; s=socket.socket(); s.connect(('localhost',65432)); s.send(b'3,5'); print(s.recv(1024).decode())"
