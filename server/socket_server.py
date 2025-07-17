import socket
import threading
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

MPI_PROCS = 4
SPARK_HOST = "localhost"
SPARK_PORT = 65432
LISTEN_PORT = 65431


def run_mpi(powmin, powmax):
    cmd = [
        "mpirun",
        "-np",
        str(MPI_PROCS),
        "--oversubscribe",
        "./jogodavida_openmp_mpi",
        str(powmin),
        str(powmax),
    ]
    logging.info(f"MPI: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return r.stdout if r.returncode == 0 else f"ERRO MPI: {r.stderr}"


def run_spark(powmin, powmax):
    with socket.socket() as s:
        s.connect((SPARK_HOST, SPARK_PORT))
        s.sendall(f"{powmin},{powmax}".encode())
        return s.recv(65536).decode()


def handle_client(conn, addr):
    try:
        logging.info(f"[SocketServer] conexão de {addr}")
        data = conn.recv(1024).decode().strip()
        logging.info(f"[SocketServer] recebeu dados: '{data}'")
        mode, smin, smax = map(str.strip, data.split(","))
        logging.info(f"[SocketServer] modo={mode}, powmin={smin}, powmax={smax}")
        logging.info(f"Conexão de {addr}")
        mode, smin, smax = map(str.strip, data.split(","))
        powmin, powmax = int(smin), int(smax)
        if mode == "mpi":
            result = run_mpi(powmin, powmax)
        elif mode == "spark":
            result = run_spark(powmin, powmax)
        else:
            result = f"Modo desconhecido '{mode}'. Use mpi ou spark.\n"
        conn.sendall(result.encode())
    except Exception as e:
        logging.error(f"{addr} erro: {e}")
        conn.sendall(f"ERRO interno: {e}\n".encode())
    finally:
        conn.close()


def main():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", LISTEN_PORT))
    sock.listen()
    logging.info(f"[SocketServer] ouvindo em 0.0.0.0:{LISTEN_PORT}")
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
