# openmp_server.py
import socket
import subprocess
import threading
import logging

HOST = "0.0.0.0"
PORT = 65433

logging.basicConfig(level=logging.INFO, format="%(asctime)s [OpenMP] %(message)s")


def handle_client(conn, addr):
    try:
        logging.info(f"Conexão recebida de {addr}")
        data = conn.recv(1024).decode().strip()
        powmin, powmax = map(int, data.split(","))
        cmd = [
            "mpirun",
            "--allow-run-as-root",
            "-np",
            "4",
            "--oversubscribe",
            "./jogodavida_mpi",
            str(powmin),
            str(powmax),
        ]
        logging.info(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout if result.returncode == 0 else f"ERRO: {result.stderr}"
        conn.sendall(output.encode())
    except Exception as e:
        logging.error(f"Erro ao processar requisição: {e}")
        conn.sendall(f"ERRO interno: {e}".encode())
    finally:
        conn.close()


def main():
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        logging.info(f"Servidor OpenMP ouvindo em {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            ).start()


if __name__ == "__main__":
    main()
