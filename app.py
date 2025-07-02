import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Pega as credenciais das variáveis de ambiente
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# --- O CÉREBRO DA IA ESTÁ AQUI ---
def processar_mensagem_ia(mensagem_usuario):
    """
    Esta é a função de IA mais simples do mundo.
    No futuro, você vai substituir isso por uma chamada para o Google Gemini,
    ChatGPT ou outra IA.
    """
    mensagem_usuario = mensagem_usuario.lower()
    
    if "olá" in mensagem_usuario or "oi" in mensagem_usuario:
        return "Olá! 👋 Sou um agente de IA. Como posso te ajudar hoje?"
    elif "horário" in mensagem_usuario or "funciona" in mensagem_usuario:
        return "Nosso horário de funcionamento é de segunda a sexta, das 9h às 18h."
    elif "obrigado" in mensagem_usuario or "obrigada" in mensagem_usuario:
        return "De nada! Se precisar de mais alguma coisa, é só chamar. 😊"
    else:
        return "Desculpe, não entendi. Poderia reformular sua pergunta?"

# Rota para a Meta verificar seu webhook
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
    return "Token de verificação inválido", 403

# Rota para receber mensagens do WhatsApp
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()
    print(json.dumps(data, indent=2)) # Útil para depuração

    if data.get("object") == "whatsapp_business_account":
        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = message['from']
            user_message_body = message['text']['body']

            # Envia a mensagem do usuário para o nosso "cérebro" de IA
            resposta_ia = processar_mensagem_ia(user_message_body)

            # Envia a resposta de volta para o usuário
            send_whatsapp_message(from_number, resposta_ia)

        except (KeyError, IndexError):
            # Caso a notificação não seja uma mensagem de usuário
            pass

    return jsonify(status="ok"), 200

def send_whatsapp_message(to_number, text_message):
    """Função para enviar uma mensagem de texto via API do WhatsApp."""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "text": {"body": text_message},
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status do envio: {response.status_code}, Resposta: {response.json()}")

if __name__ == '__main__':
    app.run(port=5000, debug=True)