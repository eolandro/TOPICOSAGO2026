import time
import random
#import os

random.seed(int(time.time()))

colores = bytes([0x00, 0x32, 0x64, 0x96, 0xC8, 0xFA])

with open("nuevo2026.ppm", "wb") as f:
    f.write(b"P6\n640 480\n255\n")

    for i in range(480):
        for j in range(640):
            for p in range(3):
                index = random.randint(0, 5)
                f.write(bytes([colores[index]]))

print("Imagen generada: nuevo2026.ppm")
#print(os.getcwd())