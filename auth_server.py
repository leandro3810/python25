from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets

app = Flask(__name__)
CORS(app)  # Permite requisições do front-end local

# Usuário/senha fixos para exemplo
USERS = {
    "leandro": "python25"
}

TOKENS = {}

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if username in USERS and USERS[username] == password:
        token = secrets.token_hex(16)
        TOKENS[token] = username
        return jsonify({"success": True, "token": token})
    return jsonify({"success": False, "message": "Usuário ou senha inválidos"}), 401

@app.route("/protected", methods=["GET"])
def protected():
    # Exemplo de rota protegida
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        if token in TOKENS:
            return jsonify({"message": f"Bem-vindo, {TOKENS[token]}!"})
    return jsonify({"message": "Não autorizado"}), 401

if __name__ == "__main__":
    app.run(debug=True)
