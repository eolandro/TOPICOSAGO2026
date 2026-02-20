from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST']) 
def login():
    datos = request.json
    print(f"Intento de login con: {datos}")
    return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)