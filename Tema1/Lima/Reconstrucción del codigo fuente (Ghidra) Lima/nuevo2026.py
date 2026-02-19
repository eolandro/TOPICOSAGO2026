import time
import random

def main():
    random.seed(int(time.time()))

    with open("nuevo2026.ppm", "wb") as f:
        f.write(b"P6\n640 480\n255\n")

        for i in range(480):
            for j in range(640):
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)

                f.write(bytes([r, g, b]))

    print("Imagen generada correctamente: nuevo2026.ppm")

if __name__ == "__main__":
    main()
