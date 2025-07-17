import socket
import threading
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler()],
)


def run_simulation(mode, powmin, powmax):
    try:
        if mode == "mpi":
            cmd = [
                "mpirun",
                "-n",
                "4",
                "./jogodavida_openmp_mpi",
                str(powmin),
                str(powmax),
            ]
        elif mode == "spark":
            cmd = [
                "spark-submit",
                "--master",
                "local[*]",
                "jogodavida_spark.py",
                str(powmin),
                str(powmax),
            ]
        else:
            return f"ERRO: modo desconhecido '{mode}'. Use 'mpi' ou 'spark'."

        logging.info(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else f"ERRO: {result.stderr}"

    except Exception as e:
        return f"EXCEÇÃO: {str(e)}"


def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            return

        parts = [p.strip() for p in data.split(",")]
        if len(parts) != 3:
            conn.sendall(
                b"Formato invalido. Envie: modo,powmin,powmax\nEx: mpi,3,10 ou spark,3,10"
            )
            return

        mode, s_powmin, s_powmax = parts
        try:
            powmin = int(s_powmin)
            powmax = int(s_powmax)
        except ValueError:
            conn.sendall(b"powmin e powmax devem ser inteiros.\n")
            return

        if not (3 <= powmin <= powmax <= 20):
            conn.sendall(
                b"Valores de pow devem estar entre 3 e 20 e powmin <= powmax.\n"
            )
            return

        output = run_simulation(mode, powmin, powmax)
        conn.sendall(output.encode())

    except Exception as e:
        logging.error(f"Erro ao atender {addr}: {e}")
    finally:
        conn.close()


def start_server(host="0.0.0.0", port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        logging.info(f"Servidor pronto em {host}:{port}")

        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            ).start()


if __name__ == "__main__":
    start_server()
