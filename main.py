from flask import Flask, request, jsonify  # ← добавить
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Flask app is working!'

@app.route('/health')
def health():
    return 'OK'

# ✅ ДОБАВИТЬ ЭТОТ ЭНДПОИНТ
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    return jsonify({"status": "received", "data": data})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
