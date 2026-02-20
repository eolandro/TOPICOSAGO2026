import time

# Paleta real de DAT_00402018
palette = [0x00, 0x32, 0x64, 0x96, 0xC8, 0xFA]

# Replicación exacta del rand() de MSVC
class MSVCRand:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF
    
    def rand(self):
        self.state = (self.state * 214013 + 2531011) & 0xFFFFFFFF
        return (self.state >> 16) & 0x7FFF

seed = int(time.time())
rng = MSVCRand(seed)

WIDTH  = 0x280  # 640
HEIGHT = 0x1e0  # 480

with open("nuevo2026.ppm", "wb") as f:
    f.write(b"P6\n640 480\n255\n")
    for row in range(HEIGHT):
        for col in range(WIDTH):
            r = palette[rng.rand() % 6]
            g = palette[rng.rand() % 6]
            b = palette[rng.rand() % 6]
            f.write(bytes([r, g, b]))

print("Listo! Archivo generado: nuevo2026.ppm")