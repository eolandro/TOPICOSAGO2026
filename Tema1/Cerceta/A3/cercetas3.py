import random
import time
def generar_imagen():
    ancho = 640
    alto = 480
    random.seed(int(time.time()))
    paleta = [0, 50, 100, 150, 200, 255]
    try:
        with open("nuevo2026.ppm", "wb") as f:
            f.write(f"P6\n{ancho} {alto}\n255\n".encode())
            for y in range(alto):
                for x in range(ancho):  # DAT_00402014 < 0x280
                    r = paleta[random.randint(0, 5)]
                    g = paleta[random.randint(0, 5)]
                    b = paleta[random.randint(0, 5)]
                    f.write(bytes([r, g, b]))
        print("Imagen 'nuevo2026.ppm' generada con éxito.")
    except Exception as e:
        print(f"Error al crear la imagen: {e}")
if __name__ == "__main__":
    generar_imagen()