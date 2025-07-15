### **Passo 2: Testando o Servidor**
1. **Salve o código** como `socket_server.py`.
2. **Execute o servidor**:
   ```bash
   python socket_server.py
   ```
3. **Teste com um cliente** (pode ser `telnet` ou `netcat`):
   ```bash
   nc localhost 65432
   ```
   Digite algo como:
   ```
   3,10,spark
   ```
   O servidor deve responder:
   ```
   Processado: powmin=3, powmax=10, engine=spark
   ```

---
