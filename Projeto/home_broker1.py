import socket 
import json
import threading
import time
import datetime
import sys
import os

horario_digital = {}
arrayPort = [5213, 5214, 5215]
portHB = 5110

def relogio():
    horario_atual = datetime.datetime.now()
    horario_digital["hora"] = int(horario_atual.hour)
    horario_digital["minuto"] = int(horario_atual.minute)
    horario_digital["segundo"] = int(horario_atual.second)
    variacao = 0
    while True:
        time.sleep(1)
        variacao+=1
        hora = horario_digital["hora"]
        minuto = horario_digital["minuto"]
        segundo = horario_digital["segundo"]
        #print(f"Horario: {hora}:{minuto}:{segundo}")
        segundo +=1
        if(variacao == 10):
            segundo+=2
            variacao = 0
        if(segundo >= 60):
            segundo = 0
            minuto = minuto+1
            if(minuto >= 60):
                minuto = 0
                hora = hora+1
                if(hora == 24):
                    hora =0
        horario_digital["hora"] = hora
        horario_digital["minuto"] = minuto
        horario_digital["segundo"] = segundo

def clientChangeStock(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #print('Conectado ao Robo')
        msg = json.dumps(data)
        s.sendall(msg.encode())    

def  clientBuySellStock(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #print('Conectado ao Robo')
        data["horario_envio"] = horario_digital
        msg = json.dumps(data)
        s.sendall(msg.encode())    
        return json.dumps(s.recv(1024).decode())

def clientOpenCloseStock(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #print('Conectado ao Robo')
        msg = json.dumps(data)
        s.sendall(msg.encode())    

def serverThreads(conn, addr):
    #print('Conexão estabelecida por', addr)
    data = json.loads(conn.recv(1024).decode()) 
    if(data["tipoMSG"] == "openStock"):
        for port in arrayPort:
            client_thread = threading.Thread(target=clientOpenCloseStock, args=('127.0.0.1', port, data))
            client_thread.start()
    elif(data["tipoMSG"] == "closeStock"):
        for port in arrayPort:
            client_thread = threading.Thread(target=clientOpenCloseStock, args=('127.0.0.1', port, data))
            client_thread.start()
    elif(data["tipoMSG"] == "comprar" or data["tipoMSG"] == "vender"):
        resp = clientBuySellStock('127.0.0.1', 5500, data)
        conn.sendall(resp.encode())
    elif(data["tipoMSG"] == "sincronizar"):
        horarioTemp = json.loads(data["horario_atual"])
        horario_digital["hora"] = horarioTemp["hora"]
        horario_digital["minuto"] = horarioTemp["minuto"]
        horario_digital["segundo"] = horarioTemp["segundo"]
    elif(data["tipoMSG"] == "changeStock"):
        emp = data["emp"]
        quant = data["quant"]
        preco = data["preco"]
        nameArq = os.path.basename(sys.argv[0]).split(".")[0]
        nameArq = "Log_Change_Bolsa_"+nameArq+".txt"
        arquivo = open(nameArq, "a")
        arquivo.write(f"Novo Valor-> emp: {emp} | quantidade: {quant}| valor: {preco}\n")
        arquivo.close()
        for port in arrayPort:
            client_thread = threading.Thread(target=clientChangeStock, args=('127.0.0.1', port, data))
            client_thread.start()
    conn.close()

def server():
    HOST = '127.0.0.1'   # Host em branco significa que o servidor pode receber solicitações de qualquer endereço.
    PORT = portHB # Porta que o servidor vai escutar.

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print('Home_Broker escutando na porta', PORT)

        while True:
            conn, addr = s.accept()
            threadServer = threading.Thread(target=serverThreads, args=(conn, addr))
            threadServer.start()

nameArq = os.path.basename(sys.argv[0]).split(".")[0]
nameArq = "Log_Change_Bolsa_"+nameArq+".txt"
arquivo = open(nameArq, "w")
arquivo.write("")
arquivo.close()
relogio_thread = threading.Thread(target=relogio)
relogio_thread.start()
server()