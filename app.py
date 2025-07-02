import os
import json
import requests
import google.generativeai as genai  # Importa a biblioteca do Gemini
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# SUAS CREDENCIAIS
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Nova credencial

# Configura a API do Gemini com sua chave
genai.configure(api_key=GEMINI_API_KEY)

# --- O NOVO CÉREBRO COM GEMINI ---
def processar_mensagem_ia(mensagem_usuario):
    try:
        # Cria o modelo
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Usamos o Flash, que é rápido e eficiente

        # Aqui você pode adicionar um contexto para o bot se comportar como você quer
        # Ex: "Você é um assistente virtual para a Pizzaria do Zé. Responda de forma amigável e ajude com o cardápio."
        prompt_com_contexto = f"Você é um assistente virtual prestativo. Responda a seguinte pergunta do usuário: '{mensagem_usuario}'"

        # Gera a resposta
        response = model.generate_content(prompt_com_contexto)

        # Extrai o texto da resposta
        return response.text

    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        return "Desculpe, estou com um problema para me conectar à minha inteligência. Tente novamente mais tarde."

# ... (o resto do seu código, como a função `verify_webhook`, continua o mesmo) ...

# Rota para receber mensagens do WhatsApp (NÃO MUDA NADA AQUI)
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()
    print(json.dumps(data, indent=2))

    if data.get("object") == "whatsapp_business_account":
        try:
            # Extrai informações da mensagem recebida
            message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = message_data['from']
            
            # --- SUPORTE PARA BOTÕES ---
            # Verifica se a mensagem veio de um clique de botão
            if 'interactive' in message_data and message_data['interactive']['type'] == 'button_reply':
                button_id = message_data['interactive']['button_reply']['id']
                user_message_body = f"O usuário clicou no botão: {button_id}" # Simula uma mensagem de texto
            # Verifica se é uma mensagem de texto normal
            elif 'text' in message_data:
                user_message_body = message_data['text']['body']
            else:
                # Ignora outros tipos de mensagem por enquanto (áudio, imagem, etc)
                return jsonify(status="ok"), 200

            # Envia a mensagem do usuário para o nosso "cérebro" de IA (Gemini)
            resposta_ia = processar_mensagem_ia(user_message_body)

            # Envia a resposta de volta para o usuário
            send_whatsapp_message(from_number, {"type": "text", "content": resposta_ia})

        except (KeyError, IndexError):
            pass

    return jsonify(status="ok"), 200

# ... (A função verify_webhook continua a mesma) ...

# --- FUNÇÃO DE ENVIO ATUALIZADA PARA SUPORTAR MAIS RECURSOS ---
def send_whatsapp_message(to_number, message_data):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number
    }

    # Constrói o corpo da mensagem com base no tipo
    if message_data["type"] == "text":
        payload["text"] = {"body": message_data["content"]}
    elif message_data["type"] == "interactive_buttons":
        payload["type"] = "interactive"
        payload["interactive"] = {
            "type": "button",
            "body": {
                "text": message_data["body_text"]
            },
            "action": {
                "buttons": message_data["buttons"] # Lista de botões
            }
        }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status do envio: {response.status_code}, Resposta: {response.json()}")

# --- EXEMPLO DE USO DA NOVA FUNÇÃO DE ENVIO COM BOTÕES ---
@app.route('/send-test-button', methods=['GET'])
def send_button_example():
    # Pega o número de teste a partir da URL, ex: /send-test-button?to=5511999998888
    to_number = request.args.get('to')
    if not to_number:
        return "Por favor, especifique o número de destino na URL com '?to=NUMERO'", 400

    # Define a estrutura dos botões
    message = {
        "type": "interactive_buttons",
        "body_text": "Olá! Gostaria de ver nosso cardápio ou falar com um atendente?",
        "buttons": [
            {
                "type": "reply",
                "reply": {
                    "id": "ver_cardapio",
                    "title": "🍕 Ver Cardápio"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "falar_atendente",
                    "title": "👩‍💼 Falar com Atendente"
                }
            }
        ]
    }
    send_whatsapp_message(to_number, message)
    return f"Mensagem com botões enviada para {to_number}", 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
