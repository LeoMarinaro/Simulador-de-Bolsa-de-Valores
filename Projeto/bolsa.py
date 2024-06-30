import socket 
import json
import threading
import time
import datetime

acoes = [{"nome": "empresa1", "quant": 50, "preco": 70},
        {"nome": "empresa2", "quant": 50, "preco": 60},
        {"nome": "empresa3", "quant": 50, "preco": 100},
        {"nome": "empresa4", "quant": 50, "preco": 20},
        {"nome": "empresa5", "quant": 50, "preco": 30}]

horario_digital = {}
#arrayPort = [5110, 5120, 5130]
arrayHost = ['127.0.0.1', '192.168.0.89']
arrayPort = [5110, 5120]
portBolsa = 5500

def WriteLogStartEnd(horario, tipo):
    tipoArq = ""
    texto = ""
    if(tipo == "start"):
        tipoArq = "w"
        texto = "Abertura da Bolsa"
    elif(tipo == "end"):
        tipoArq = "a"
        texto = "Fechamento da Bolsa"
    arquivo = open("Bolsa_Log_Start_End.txt", tipoArq)
    tempHora = int(horario["hora"])
    tempMinuto = int(horario["minuto"])
    tempSegundo = int(horario["segundo"])
    if(tempHora<10):
        tempHora = "0"+str(tempHora)
    if(tempMinuto<10):
        tempMinuto = "0"+str(tempMinuto)
    if(tempSegundo<10):
        tempSegundo = "0"+str(tempSegundo)
    arquivo.write(f"{texto}\n")
    arquivo.write(f"{tempHora}:{tempMinuto}:{tempSegundo}\n")
    arquivo.close()

def WriteLogBolsa():
    time.sleep(3)
    arquivo = open("Bolsa_Log_Acoes.txt", "w")
    for acao in acoes:
        nome = acao["nome"]
        quant = acao["quant"]
        preco = acao["preco"]
        arquivo.write(f"Empresa: {nome} | Papeis: {quant} | Valor: {preco}\n")
    arquivo.close()

def clientCloseThread(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #print('Conectado ao Home Breaker para Finalizar')
        relogio_thread = threading.Thread(target=WriteLogBolsa)
        relogio_thread.start()
        print("Bolsa Fechada")
        msg = json.dumps({"tipoMSG": "closeStock"})
        s.sendall(msg.encode())

def relogio():
    horario_atual = datetime.datetime.now()
    horario_digital["hora"] = int(horario_atual.hour)
    horario_digital["minuto"] = int(horario_atual.minute)
    horario_digital["segundo"] = int(horario_atual.second)
    WriteLogStartEnd(horario_digital, "start")
    duracao = 120
    while True:
        time.sleep(1)
        hora = horario_digital["hora"]
        minuto = horario_digital["minuto"]
        segundo = horario_digital["segundo"]
        segundo +=1
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
        duracao -= 1
        if(duracao <= 0):
            for x in range(0,2):
                client_thread = threading.Thread(target=clientCloseThread, args=(arrayHost[x], arrayPort[x]))
                client_thread.start()
            WriteLogStartEnd(horario_digital, "end")
            break

def clientHorarioThread(host, port, AntHora, AntMin, AntSegundo):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #print('Conectado ao Home Breaker')

        msg = json.dumps({"tipoMSG": "sincronizar", "horario_atual": json.dumps(horario_digital)})
        s.sendall(msg.encode())
        data = s.recv(1024)
        #print('Horario Sincronizado')
        hora = horario_digital["hora"]
        minuto = horario_digital["minuto"]
        segundo = horario_digital["segundo"]
        arquivo = open("Bolsa_Log_Horarios.txt", "a")
        arquivo.write("============================\n")
        arquivo.write(f"Horario Antigo: {AntHora}:{AntMin}:{AntSegundo}\n")
        arquivo.write(f"Horario de Sincronizacao: {hora}:{minuto}:{segundo}\n")
        arquivo.write("============================\n")
        arquivo.close()

def clientHorario(hora, min, segundo):
    for x in range(0,2):
        client_thread = threading.Thread(target=clientHorarioThread, args=(arrayHost[x], arrayPort[x], hora, min, segundo))
        client_thread.start()

def clientChangeThread(host, port, emp, novoPreco, novoQuant):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #print('Conectado ao Home Breaker para Finalizar')
        msg = json.dumps({"tipoMSG": "changeStock", "emp":emp, "quant":novoQuant, "preco":novoPreco})
        s.sendall(msg.encode())

def clientChange(emp, novoPreco, novoQuant):
    for x in range(0,2):
        client_thread = threading.Thread(target=clientChangeThread, args=(arrayHost[x],  arrayPort[x], emp, novoPreco, novoQuant))
        client_thread.start()

def clientOpenThread(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("tentando")
        s.connect((host, port))
        print('Conectado ao Home Breaker para Finalizar')
        msg = json.dumps({"tipoMSG": "openStock", "listaAcoes": json.dumps(acoes)})
        s.sendall(msg.encode())

def clientOpenStock():
    for x in range(0,2):
        print("Host: "+arrayHost[x])
        print("Host: "+str(arrayPort[x]))
        client_thread = threading.Thread(target=clientOpenThread, args=(arrayHost[x], arrayPort[x]))
        client_thread.start()

def serverThreads(conn, addr):
    #print('Conexão estabelecida por', addr)
    data = json.loads(conn.recv(1024).decode())
    emp = data["emp"]
    quant = data["quant"]
    msg = ""
    dif = data["horario_envio"]["segundo"] - horario_digital["segundo"]
    if(data["horario_envio"]["hora"] != horario_digital["hora"] or data["horario_envio"]["minuto"] != horario_digital["minuto"] or dif > 1 or dif < -1):
        client_horario_thread = threading.Thread(target=clientHorario, args=(data["horario_envio"]["hora"], data["horario_envio"]["minuto"], data["horario_envio"]["segundo"]))
        client_horario_thread.start()
    if(data["tipoMSG"] == "comprar"):
        for acao in acoes:
            if(acao["nome"] == emp):
                if(acao["quant"] >= quant):
                    antPreco = acao["preco"]
                    acao["quant"] -= quant
                    acao["preco"] += quant
                    novoPreco = acao["preco"]
                    novoQuant = acao["quant"]
                    #print("Bolsa vendeu "+str(quant)+" papeis da "+nomeEmp+ " para o robo"+data["nomeArq"])
                    msg = {"tipoMSG":"comprado", "emp":emp,"quant":quant,"antPreco":antPreco,"novoPreco":novoPreco, "horario_aceito":horario_digital}
                    client_thread = threading.Thread(target=clientChange, args=(emp, novoPreco, novoQuant))
                    client_thread.start()
                else:
                    antPreco = acao["preco"]
                    #print("Bolsa não vendeu acoes da "+nomeEmp+" para o robo"+data["nomeArq"])
                    msg = {"tipoMSG":"naocomprado", "emp":emp,"quant":quant,"antPreco":antPreco, "horario_aceito":horario_digital}
                    break        
    elif(data["tipoMSG"] == "vender"):
        for acao in acoes:
            if(acao["nome"] == emp):
                antPreco = acao["preco"]
                acao["quant"] += quant
                acao["preco"] -= quant
                if(acao["preco"] < 1):
                    acao["preco"] = 1
                novoPreco = acao["preco"]
                novoQuant = acao["quant"]
                #print("Bolsa comprou "+str(quant)+"papeis da "+nomeEmp+ " para o robo"+data["nomeArq"])
                msg = {"tipoMSG":"vendido", "emp":emp,"quant":quant,"antPreco":antPreco,"novoPreco":novoPreco, "horario_aceito":horario_digital}
                client_thread = threading.Thread(target=clientChange, args=(emp, novoPreco, novoQuant))
                client_thread.start()
                break
    conn.sendall(json.dumps(msg).encode())
    conn.close()

def server():
    HOST = '127.0.0.1'   # Host em branco significa que o servidor pode receber solicitações de qualquer endereço.
    PORT = portBolsa # Porta que o servidor vai escutar.

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print('Bolsa escutando na porta', PORT)

        while True:
            conn, addr = s.accept()
            threadServer = threading.Thread(target=serverThreads, args=(conn, addr))
            threadServer.start()

arquivo = open("Bolsa_Log_Horarios.txt", "w")
arquivo.write("")
arquivo.close()
relogio_thread = threading.Thread(target=relogio)
relogio_thread.start()
client_thread = threading.Thread(target=clientOpenStock)
client_thread.start()
server()