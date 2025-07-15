import socket
import threading
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

def run_simulation(powmin, powmax):
    try:
        cmd = [
            'mpirun', '-n', '4',
            './jogo_hibrido', str(powmin), str(powmax)
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout if result.returncode == 0 else f"ERRO: {result.stderr}"
    except Exception as e:
        return f"EXCEÇÃO: {str(e)}"

def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            return
            
        powmin, powmax = map(int, data.split(','))
        if not (3 <= powmin <= powmax <= 10):
            conn.sendall(b"Valores devem ser entre 3 e 10")
            return
            
        output = run_simulation(powmin, powmax)
        conn.sendall(output.encode())
        
    except Exception as e:
        logging.error(f"Erro com {addr}: {e}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 65432))
        s.listen()
        logging.info("Servidor pronto na porta 65432")
        
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == '__main__':
    start_server()