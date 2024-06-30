import socket 
import json
import threading
import time
import datetime
import sys
import os
import random

acoesBolsa = []
acoesRobo = []
trabalhando = False
cooldown = 10
porta = 5224
portaHB = 5120

def compraVenda(num):
    if(num == 0):
        return 0
    else:
        return random.randint(0, 1) #0 = compra | 1 = venda
    
def permiteCompra(num):
    if(num == 0):
        podeComprar = False
        for item in acoesBolsa:
            if(item["quant"]> 0):
                podeComprar = True
        if(podeComprar):
            return 0
        else:
            return 1
    else:
        return 1

def delAcoe(nome, quant):
    index = 0
    indexFinal = -1
    for acao in acoesRobo:
        if(nome == acao["nome"]):
            acao["quant"] -= quant
            if(int(acao["quant"]) == 0):
                indexFinal = index
        index += 1
    if(indexFinal != -1):
        acoesRobo.pop(indexFinal)

def compraAcao():
    empTemp = -1
    while True:
        empTemp = random.randint(0, len(acoesBolsa)-1)
        if(int(acoesBolsa[empTemp]["quant"]) > 0):
            break
    nomeCompra = acoesBolsa[empTemp]["nome"]
    quantCompra = random.randint(1, acoesBolsa[empTemp]["quant"])
    msg = json.dumps({"tipoMSG":"comprar","emp": nomeCompra, "quant":quantCompra}) 
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', portaHB))
        #print('Conectado ao Robo')
        s.sendall(msg.encode())
        return json.loads(s.recv(1024).decode())

def vendeAcao():
    empTemp = random.randint(0, len(acoesRobo)-1)
    nomeVenda = acoesRobo[empTemp]["nome"]
    quantVenda = random.randint(1, acoesRobo[empTemp]["quant"])
    msg = json.dumps({"tipoMSG":"vender","emp": nomeVenda, "quant":quantVenda})
    delAcoe(nomeVenda, quantVenda)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', portaHB))
        #print('Conectado ao Robo')
        s.sendall(msg.encode())  
        return json.loads(s.recv(1024).decode())  

def conclusao(resp):
    emp = resp["emp"]
    quant = resp["quant"]
    antPreco = resp["antPreco"]
    nameArq = os.path.basename(sys.argv[0]).split(".")[0]
    nameArq = "Log_Transaçoes_"+nameArq+".txt"
    arquivo = open(nameArq, "a")
    hora = resp["horario_aceito"]["hora"]
    min = resp["horario_aceito"]["minuto"]
    seg = resp["horario_aceito"]["segundo"]
    if(resp["tipoMSG"] == "comprado"):
        semDados = True
        for acao in acoesRobo:
            if(emp == acao["nome"]):
                acao["quant"] += quant
                semDados = False
        if(semDados):
            acoesRobo.append({"nome":emp, "quant":quant})
        arquivo.write(f"Bolsa aceitou a solicitacao de compra do Robo de {quant} acoes por {antPreco} da {emp} | Horario de Envio Bolsa: {hora}:{min}:{seg}\n")
    elif(resp["tipoMSG"] == "vendido"):
        arquivo.write(f"Bolsa aceitou a solicitacao de venda do Robo de {quant} acoes por {antPreco} {emp} | Horario de Envio Bolsa: {hora}:{min}:{seg}\n")
    elif(resp["tipoMSG"] == "naocomprado"):
        arquivo.write(f"Bolsa negou a solicitacao de compra do Robo | Horario de Envio Bolsa: {hora}:{min}:{seg}\n")
    arquivo.close()
    
def robotWork():
    while(trabalhando):
        time.sleep(cooldown)
        varCompraVenda = compraVenda(len(acoesRobo))
        varCompraVenda = permiteCompra(varCompraVenda)
        resp = ""
        if(varCompraVenda == 0):
            resp = compraAcao()
        elif(varCompraVenda == 1):
            resp = vendeAcao()
        conclusao(json.loads(resp))

def robot():
    while True:
        if(trabalhando):
            robotWork()
            break
    print("Bolsa Fechada")
    time.sleep(2)
    name = os.path.basename(sys.argv[0]).split(".")[0]
    name = "Log_"+name+".txt"
    arquivo = open(name, "w")
    arquivo.write("")
    arquivo.close()
    arrayEmp = ["empresa1","empresa2","empresa3","empresa4","empresa5"]
    arquivo = open(name, "a")
    for nomEmp in arrayEmp:
        for acao in acoesRobo:
            if(nomEmp == acao["nome"]):
                empTemp = acao["nome"]
                quantTemp = acao["quant"]
                arquivo.write(f"Empresa: {empTemp} | Quantidade: {quantTemp}\n")
    arquivo.close()   
    if(len(acoesRobo) == 0):
        arquivo = open(name, "w")
        arquivo.write("Sem Acoes")
        arquivo.close()

def serverThreads(conn, addr):
    global trabalhando
    #print('Conexão estabelecida por', addr)
    data = json.loads(conn.recv(1024).decode()) 
    if(data["tipoMSG"] == "openStock"):
        dictAcoes = json.loads(data["listaAcoes"])
        for acoe in dictAcoes:
            acoesBolsa.append({"nome":acoe["nome"], "quant":acoe["quant"]})
        trabalhando = True
    elif(data["tipoMSG"] == "closeStock"):
        trabalhando = False
        if(len(acoesRobo) == 0):
            arquivo = open(name, "a")
            arquivo.write(f"Sem Ações")
            arquivo.close()
    elif(data["tipoMSG"] == "changeStock"):
        for acao in acoesBolsa:
            if(data["emp"] == acao["nome"]):
                acao["quant"] = data["quant"]
    conn.close()

def server():
    HOST = '127.0.0.1'   # Host em branco significa que o servidor pode receber solicitações de qualquer endereço.
    PORT = porta # Porta que o servidor vai escutar.

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print('Robo escutando na porta', PORT)

        while True:
            conn, addr = s.accept()
            threadServer = threading.Thread(target=serverThreads, args=(conn, addr))
            threadServer.start()

name = os.path.basename(sys.argv[0]).split(".")[0]
name = "Log_Transaçoes_"+name+".txt"
arquivo = open(name, "w")
arquivo.write("")
arquivo.close()
robo_thread = threading.Thread(target=robot)
robo_thread.start()
server()