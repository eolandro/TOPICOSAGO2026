import random
import time

# Paleta de colores
paleta = [0, 50, 100, 150, 200, 250]

# Inicializar semilla
random.seed(time.time())

with open("nuevo2026_.ppm", "wb") as archivo:
    archivo.write(b"P6\n640 480\n255\n")

    # Img 480 x 640
    for i in range(480):
        for j in range(640):
            r = paleta[random.randint(0, 5)]
            g = paleta[random.randint(0, 5)]
            b = paleta[random.randint(0, 5)]
            archivo.write(bytes([r, g, b]))

print("Imagen 'nuevo2026.ppm' generada exitosamente.")
