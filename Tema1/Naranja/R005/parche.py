# Importamos lo necesario del framework Flask
# Flask -> para crear el servidor
# request -> para obtener los datos que envía el cliente
# jsonify -> para devolver respuestas en formato JSON
from flask import Flask, request, jsonify


# Creamos la aplicación Flask
# __name__ le dice a Flask cuál es el archivo principal
app = Flask(__name__)


"""

VIDEO DE PRUEBA QUE SI FUNCIONA:

https://drive.google.com/file/d/1htNhwKmXgTxasEJHI_y8ZiVBSWqrO8QX/view?usp=sharing
"""




# Definimos la ruta /login
# Esto significa que cuando alguien haga una petición POST a:
# http://IP:8000/login
# se ejecutará la función login()
@app.route('/login', methods=['POST'])
def login():
    
    # request.json obtiene el cuerpo de la petición en formato JSON
    # Por ejemplo si envían:
    # { "usuario": "maria", "password": "1234" }
    # entonces "datos" guardará ese diccionario
    datos = request.json

    # Esto imprime en la consola del servidor
    # Sirve para ver qué está enviando el cliente
    print("Datos recibidos:", datos)

    # Aquí devolvemos una respuesta al cliente en formato JSON
    # jsonify convierte el diccionario en una respuesta HTTP válida
    return jsonify({
        
        # "R": 200 es un código lógico de éxito (como decir OK)
        "R": 200,

        # "D": 41 es un valor que decides mantener
        # (probablemente tu programa cliente lo espera)
        "D": 41,

        # Mensaje personalizado
        # Este login siempre será exitoso
        # NO se valida usuario ni contraseña
        "message": "Login exitoso con cualquier usuario y contraseña"
    })


# Esta condición verifica que el archivo se esté ejecutando directamente
# y no siendo importado como módulo
if __name__ == '__main__':

    # Iniciamos el servidor
    # host='0.0.0.0' permite conexiones desde cualquier IP
    # port=8000 indica el puerto donde escuchará
    # Entonces quedará disponible en:
    # http://127.0.0.1:8000
    app.run(host='0.0.0.0', port=8000)
