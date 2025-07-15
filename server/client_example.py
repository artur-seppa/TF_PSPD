import socket
import json

HOST = 'localhost'
PORT = 65432

def send_request(powmin, powmax):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        
        # Envia como string simples
        s.sendall(f"{powmin},{powmax}".encode('utf-8'))
        
        # Ou como JSON
        # data = json.dumps({"powmin": powmin, "powmax": powmax})
        # s.sendall(data.encode('utf-8'))
        
        response = s.recv(4096).decode('utf-8')
        print("Resposta do servidor:\n", response)

if __name__ == "__main__":
    send_request(3, 6)  # Teste com matrizes de 8x8 até 64x64