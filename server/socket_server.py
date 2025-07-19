import socket
import threading
import subprocess
import logging
import uuid
import tempfile
import os
from elasticsearch import Elasticsearch

# ===== CONFIGURAÇÕES =====
LISTEN_PORT = 65431
MPI_PROCS = 4
SPARK_HOST = "spark-engine-service"
SPARK_PORT = 65432


ELASTIC_URL = "http://elasticsearch.monitoring.svc.cluster.local:9200"
ELASTIC_USER = "elastic"
ELASTIC_PASS = "changeme"

es = Elasticsearch([ELASTIC_URL], basic_auth=(ELASTIC_USER, ELASTIC_PASS))


def log_to_elastic(event, data):
    try:
        doc = {
            "event": event,
            "data": data,
            "host": os.environ.get("HOSTNAME"),
            "uuid": str(uuid.uuid4()),
        }
        es.index(index="socket-logs", document=doc)
    except Exception as e:
        logging.error(f"Falha ao enviar log ao Elasticsearch: {e}")


logging.basicConfig(level=logging.INFO, format="%(asctime)s [SocketServer] %(message)s")


def run_mpi_job(powmin, powmax):
    job_id = f"jogodavida-job-{uuid.uuid4().hex[:8]}"
    job_yaml = f"""
apiVersion: batch/v1
kind: Job
metadata:
  name: {job_id}
spec:
  template:
    spec:
      containers:
        - name: jogodavida
          image: pedroblome/pspd_trabalho:openmp
          command: ["mpirun", "--allow-run-as-root", "-np", "{MPI_PROCS}", "./jogodavida_mpi", "{powmin}", "{powmax}"]
      restartPolicy: Never
  backoffLimit: 0
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(job_yaml)
        tmpfile = f.name

    try:
        subprocess.run(["kubectl", "apply", "-f", tmpfile], check=True)

        # Aguarda o Job terminar
        subprocess.run(
            [
                "kubectl",
                "wait",
                "--for=condition=complete",
                f"job/{job_id}",
                "--timeout=120s",
            ],
            check=True,
        )

        # Captura nome do pod do Job
        pod_name = (
            subprocess.check_output(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-l",
                    f"job-name={job_id}",
                    "-o",
                    "jsonpath={.items[0].metadata.name}",
                ]
            )
            .decode()
            .strip()
        )

        # Captura logs
        logs = subprocess.check_output(["kubectl", "logs", pod_name]).decode()
        return logs

    except subprocess.CalledProcessError as e:
        return f"ERRO no Job MPI: {e}"

    finally:
        os.remove(tmpfile)
        subprocess.run(["kubectl", "delete", "job", job_id], stdout=subprocess.DEVNULL)


def run_spark(powmin, powmax):
    print(
        f"Conectando ao Spark em {SPARK_HOST}:{SPARK_PORT} com parâmetros {powmin}, {powmax}"
    )
    try:
        with socket.socket() as s:
            s.connect((SPARK_HOST, SPARK_PORT))
            s.sendall(f"{powmin},{powmax}".encode())
            return s.recv(65536).decode()
    except Exception as e:
        return f"ERRO ao conectar ao Spark: {e}"


def handle_client(conn, addr):
    try:
        logging.info(f"Conexão recebida de {addr}")
        data = conn.recv(1024).decode().strip()
        logging.info(f"Dados recebidos: '{data}'")

        mode, smin, smax = map(str.strip, data.split(","))
        powmin, powmax = int(smin), int(smax)

        if mode == "mpi":
            result = run_mpi_job(powmin, powmax)
        elif mode == "spark":
            result = run_spark(powmin, powmax)
        else:
            result = f"Modo desconhecido '{mode}'. Use 'mpi' ou 'spark'."

        conn.sendall(result.encode())

    except Exception as e:
        logging.error(f"Erro: {e}")
        conn.sendall(f"ERRO interno: {e}".encode())
    finally:
        conn.close()


def main():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", LISTEN_PORT))
    sock.listen()
    logging.info(f"SocketServer ouvindo em 0.0.0.0:{LISTEN_PORT}")
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
