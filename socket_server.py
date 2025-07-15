import socket
import threading

# Configurações do servidor
HOST = '0.0.0.0'  # Escuta em todas as interfaces
PORT = 65432      # Porta padrão

def handle_client(conn, addr):
    """Função que lida com cada cliente em uma thread separada."""
    print(f"[NOVA CONEXÃO] {addr} conectado.")
    
    try:
        while True:
            # Recebe dados do cliente (formato esperado: "POWMIN,POWMAX,ENGINE")
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break  # Cliente desconectou
            
            print(f"[{addr}] Dados recebidos: {data}")
            
            # Processa a requisição (exemplo: "3,10,spark")
            powmin, powmax, engine = data.split(',')
            
            # TODO: Chamar o engine adequado (Spark ou OpenMP/MPI)
            # Por enquanto, só simulamos uma resposta
            response = f"Processado: powmin={powmin}, powmax={powmax}, engine={engine}"
            
            # Envia a resposta de volta ao cliente
            conn.sendall(response.encode('utf-8'))
            
    except Exception as e:
        print(f"[ERRO] {addr}: {e}")
    finally:
        conn.close()
        print(f"[CONEXÃO ENCERRADA] {addr}")

def start_server():
    """Inicia o servidor socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVIDOR INICIADO] Escutando em {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()  # Aceita nova conexão
            # Cria uma thread para lidar com o cliente
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[CONEXÕES ATIVAS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()