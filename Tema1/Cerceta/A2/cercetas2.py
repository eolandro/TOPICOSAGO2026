from pathlib import Path

OFFSET = 0x248
ARCHIVO_ORIGINAL = "prueba.exe"
ARCHIVO_PARCHEADO = "cercetas_ejemplo_patch.exe"

def parchear(origen: Path, destino: Path, offset: int):
    import shutil
    shutil.copy2(origen, destino)

    with destino.open('r+b') as f:
        f.seek(offset)
        byte_viejo = f.read(1)
        print(f"Se cambiara {byte_viejo} por (b'\\x00')")
        f.seek(offset)
        f.write(b'\x00')

    print(f"Su parche fue aplicado ejecute {destino}")

if __name__ == '__main__':
    base = Path.cwd()
    origen = base / ARCHIVO_ORIGINAL
    destino = base / ARCHIVO_PARCHEADO

    if not origen.exists():
        print("No se encontro el archivo a parchar")
    else:
        parchear(origen, destino, OFFSET)