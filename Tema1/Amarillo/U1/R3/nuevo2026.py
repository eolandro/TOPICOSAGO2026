import time
import random

from pathlib import Path

random.seed(time.time())

with open(f"{Path.cwd()}/Ruido/nuevo2026.ppm", "+wb") as archivo:
    archivo.write(b"P6\n640 480\n255\n")

    paleta = [0, 50, 100, 150, 200, 250]

    for i in range(480):
        for j in range(640):
            color = random.randint(0, 5)
            archivo.write(bytes([paleta[color]]))

            color = random.randint(0, 5)
            archivo.write(bytes([paleta[color]]))

            color = random.randint(0, 5)
            archivo.write(bytes([paleta[color]]))

    archivo.close()
