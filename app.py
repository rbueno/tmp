import re
import requests
import subprocess
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import time
import qrcode
from escpos.printer import Network
from PIL import Image, ImageFilter, ImageEnhance
import os
import subprocess
import json

# Data e hora atuais
now = datetime.now()

# Subtrai 1 dia e adiciona 21 horas
adjusted_time = now - timedelta(days=1) + timedelta(hours=21)

# Formata a data ajustada
formatted_time = adjusted_time.strftime('%H:%M:%S')
formatted_date = adjusted_time.strftime('%d/%m/%Y')


# Defina o IP da impressora
ip_impressoras = {
    "entrada1": "10.70.0.22",
    "entrada2": "10.70.0.248"
}

# Associando cancela aos IPs das câmeras
cancelas_name = {
    "entrada1": "10.70.0.12",
    "entrada2": "10.70.0.13"
}

# Função para redimensionar a imagem
def redimensionar_imagem(caminho_imagem, tamanho=(400, 250)):
    try:
        img = Image.open(caminho_imagem)
        img = img.resize(tamanho, Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        img.save(caminho_imagem)
    except Exception as e:
        print(f"Erro ao redimensionar a imagem: {e}")

# Função para gerar o QR Code
def gerar_qrcode(dados, tamanho=(300, 300)):
    try:
        qr = qrcode.make(dados)
        qr = qr.resize(tamanho, Image.LANCZOS)
        qr.save("qrcode_ticket.png")
    except Exception as e:
        print(f"Erro ao gerar o QR Code: {e}")

# Função para imprimir o ticket
def imprimir_ticket(conteudo, caminho_imagem, ip_impressora):
    try:
        p = Network(ip_impressora)
        redimensionar_imagem(caminho_imagem, tamanho=(400, 250))
        gerar_qrcode(conteudo, tamanho=(300, 300))
        p.image(caminho_imagem)
        p.text("\n")
        p.set(align='center')
        p.text("TICKET DE ESTACIONAMENTO\n")
        p.text("-----------------------------\n")
        p.text(conteudo)
        p.text(f"Data: {formatted_date}\n")
        p.text("-----------------------------\n")
        p.image("qrcode_ticket.png")
        p.text("Obrigado por utilizar nossos serviços!\n")
        p.cut(mode='FULL')
        p.close()
    except Exception as e:
        print(f"Erro ao imprimir: {e}")

# Função para imprimir o cupom-cliente
def imprimir_cupom(dados_pagamento, ip_impressora):
    try:
        p = Network(ip_impressora)
        # Conteúdo do cupom
        conteudo_cupom = (
            f"DADOS RECEBIDOS:\n"
            f"{dados_pagamento['imprimir']}\n"
        )

        # p.set(align='center')
        p.text(conteudo_cupom)
        p.cut(mode='FULL')
        p.close()
    except Exception as e:
        print(f"Erro ao imprimir o cupom: {e}")

# Função para salvar a imagem com a extensão correta se estiver faltando
def salvar_com_extensao(caminho_imagem):
    try:
        img = Image.open(caminho_imagem)
        if img.format == 'JPEG' and not caminho_imagem.lower().endswith('.jpeg'):
            novo_caminho = caminho_imagem + ".jpeg"
            os.rename(caminho_imagem, novo_caminho)
            return novo_caminho
        return caminho_imagem
    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")
        return None

def identificar_placa(texto):
    formatos_validos = [
        r'^[A-Z]{3}-?\d{4}$',   # Formato antigo: AAA-0000 ou AAA0000
        r'^[A-Z]{3}\d[A-Z]\d{2}$',  # Formato Mercosul: AAA0A00
        r'^[A-Z]{3}-?\d[A-Z]-?\d{2}$'  # Formato Mercosul com hífen opcional: AAA0A00 ou AAA-0A-00
    ]

    texto = texto.strip().upper()

    # Verifica se o texto corresponde a algum dos formatos válidos
    return any(re.match(formato, texto) for formato in formatos_validos)

def open_script(cancela):
    # Obtém o IP da câmera pela cancela
    cancela_ip = cancelas_name.get(cancela)
    if not cancela_ip:
        print(f"Operador '{cancela}' não encontrado.")
        return

    script_path = "./configurar.sh"
    result = subprocess.run(["bash", script_path, cancela_ip], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro ao executar o script shell: {result.stderr}")
    else:
        print(f"Cancela do {cancela} controlada com sucesso.")

# Dicionário para armazenar as placas dos veículos que já passaram pela entrada
veiculos_registrados = {}

# Função para verificar e registrar a entrada do veículo
def registrar_entrada(placa, tipo_entrada):
    # Verifica se a placa já foi registrada
    if placa in veiculos_registrados:
        # Se já foi registrada, retorna False para não imprimir novamente
        return False
    else:
        # Se não foi registrada, marca como registrada e imprime o ticket
        veiculos_registrados[placa] = True
        return True

# Inicializar a aplicação Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Rota para o webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    #print("Entrou no webhook")
    #data = request.form
    #print("Leu o request.form")
    #text_fmt = data.get("text_fmt")
    #print("Leu o text_fmt", text_fmt)
    #camera_name = data.get('camera_name')
    #print("Leu a camera", camera_name)
    #response = requests.post("http://127.0.0.1:3000/api/webhook", json={
     #"message": "start",
     #"placa": placa,
     #"cameraName" : camera_name
     #}
    #)
    data = request.form
    imagem = request.files.get('image')

    print(f"Dados recebidos: {data}")

    # Verificar se a imagem foi enviada
    if not imagem:
        return jsonify({"error": "Nenhuma imagem foi enviada"}), 400

    # Salvar a imagem temporariamente no servidor
    caminho_imagem = os.path.join('/tmp', imagem.filename)
    imagem.save(caminho_imagem)

    caminho_imagem = salvar_com_extensao(caminho_imagem)
    if not caminho_imagem:
        return jsonify({"error": "Falha ao processar a imagem"}), 500

    # Verificar o formato da placa
    placa = data["text_fmt"]
    print(f"Placa recebida: {placa}")
    if not identificar_placa(placa):
        return jsonify({"error": "Formato de placa inválido"}), 400

    camera_name = data.get('camera_name')
    tipo_entrada = 'ENTRY' if camera_name.startswith('entrada') else 'EXIT'

    ip_impressora = ip_impressoras.get(camera_name)
    if not ip_impressora:
        print(f"Ip Impressora '{camera_name}' não encontrado.")
        return

    print(f"----------1------------")
    try:
        if tipo_entrada == "ENTRY":

            # Verifica se o veículo já está registrado
            if registrar_entrada(placa, tipo_entrada):
                print(f"------------------2---------------")
                # Conteúdo do ticket
                conteudo_ticket = f"Veículo: {placa}\nEntrada: {formatted_time}\n"
                imprimir_ticket(conteudo_ticket, caminho_imagem, ip_impressora)

                # Registrar a entrada do veículo
                response = requests.post("http://127.0.0.1:3000/api/webhook", json={
                      "message": "start",
                      "placa": placa,
                      "preco": "30,00",
                      "cameraName" : camera_name
                  }
                )
                if response.status_code not in [200, 201]:
                    print(f"Erro ao registrar entrada: {response.status_code}, {response.text}")


        else:  # tipo_entrada == "EXIT"
            exit = data.get('text_fmt')
            if exit:
                exit_datetime = datetime.strptime(exit, "%Y-%m-%dT%H:%M:%S.%fZ")
                response = requests.post("http://localhost:3000/api/ispaid", json={"text_fmt": exit})
                if response.status_code != 201:
                    print(f"Erro ao verificar pagamento: {response.status_code}, {response.text}")
                    return jsonify({"error": "Erro ao verificar pagamento"}), 500

                response2 = requests.post("http://localhost:3000/api/exit", json={
                    "text_fmt": exit,
                    "exitAt": exit_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                })
                if response2.status_code != 201:
                    print(f"Erro ao registrar saída: {response2.status_code}, {response2.text}")
                open_script()

    except Exception as e:
        print(f"Erro no processamento: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Dados recebidos e processados com sucesso", "data": data}), 200


@app.route('/webhook-pagamento', methods=['POST'])
def webhook_pagamento():
    data = request.json
    cancela = data.get("cancela")

    print("Dados recebidos:", data)

    # Aqui vamos assumir que os dados do pagamento incluem 'imprimir'
    ip_impressora = ip_impressoras.get(cancela)
    if not ip_impressora:
        print(f"Operador '{cancela}' não encontrado.")
        return
    if 'imprimir' in data:
        imprimir_cupom(data, ip_impressora)
    else:
        return jsonify({"error": "Dados de pagamento incompletos"}), 400

    return jsonify({"message": "Dados recebidos com sucesso"}), 200


# Rota para liberar ação manual
@app.route('/liberar/<cancela>', methods=['POST'])
def liberar(cancela):
    if cancela not in cancelas_name:
        return jsonify({"error": "Cancela inválida"}), 400
    open_script(cancela)
    return jsonify({"message": "OK"}), 200


if __name__ == '__main__':
    app.run(debug=True)
