from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    datos = request.json
    print("Datos recibidos:", datos)  # sigue mostrando lo que envían
    # Puedes personalizar la respuesta si quieres
    return jsonify({
        "R": 200,   # código de éxito
        "D": 41,    # valor que quieras mantener
        "message": "Login exitoso con cualquier usuario y contraseña"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
