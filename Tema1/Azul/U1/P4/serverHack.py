from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    return jsonify({"R": 200}), 200

if __name__ == '__main__':
    app.run(host='45.76.173.114', port=8080)