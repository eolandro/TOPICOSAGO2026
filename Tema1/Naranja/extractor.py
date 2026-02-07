
# Archivo donde están incrustados todos los datos
ARCHIVO = "naranja.mpeg"

# Aquí se guardan las regiones del archivo que ya fueron usadas
# para que no se empalmen las extracciones
ocupados = []


def esta_encimado(ini, fin):
    # Revisa si una región ya fue usada antes
    for a, b in ocupados:
        if ini >= a and fin <= b:
            return True
    return False


# ==========================
# JPG 
def extraer_jpg():
    # Leer todo el archivo en binario
    with open(ARCHIVO, "rb") as f:
        data = f.read()

    pos = 0
    contador = 0

    # Posibles encabezados reales de imágenes JPG
    headers_jpg = [
        b"\xFF\xD8\xFF\xE0",  # JFIF
        b"\xFF\xD8\xFF\xE1",  # EXIF
        b"\xFF\xD8\xFF\xE2",
        b"\xFF\xD8\xFF\xDB",
        b"\xFF\xD8\xFF\xEE",
    ]

    # Buscar imágenes mientras haya datos
    while pos < len(data):
        ini = -1
        header_encontrado = None

        # Buscar el JPG más cercano desde la posición actual
        for h in headers_jpg:
            p = data.find(h, pos)
            if p != -1 and (ini == -1 or p < ini):
                ini = p
                header_encontrado = h

        if ini == -1:
            break

        # Buscar el final del JPG (FFD9)
        fin = ini + len(header_encontrado)
        while True:
            fin = data.find(b"\xFF\xD9", fin)
            if fin == -1:
                pos = ini + 1
                break

            fin += 2

            # Verificar que no empiece otro JPG antes
            siguiente = len(data)
            for h in headers_jpg:
                t = data.find(h, ini + len(header_encontrado))
                if t != -1 and t < siguiente:
                    siguiente = t

            if siguiente >= fin:
                break

        # Validar que sea una imagen real
        if fin != -1 and fin > ini:
            bloque = data[ini:fin]
            if (
                fin - ini > 1024 and              # tamaño mínimo
                b"\xFF\xDA" in bloque[:10000] and # marcador SOS
                not esta_encimado(ini, fin)
            ):
                contador += 1
                with open(f"{contador}.jpg", "wb") as out:
                    out.write(bloque)

                ocupados.append((ini, fin))
                print(f"[✔] JPG #{contador}")

        pos = ini + 1


# ==========================
# MP3
def extraer_mp3():
    with open(ARCHIVO, "rb") as f:
        data = f.read()

    inicio = None
    for sig in (b"ID3", b"\xFF\xFB", b"\xFF\xF3", b"\xFF\xF2"):
        p = data.find(sig)
        if p != -1:
            inicio = p
            break

    if inicio is None:
        return

    cortes = [
        b"\xFF\xD8\xFF",
        b"OggS",
        b"\x00\x00\x20\x74",
        b"\x50\x4B\x03\x04"
    ]

    fin = len(data)
    for c in cortes:
        p = data.find(c, inicio + 4)
        if p != -1 and p < fin:
            fin = p

    if fin - inicio > 30000 and not esta_encimado(inicio, fin):
        with open("3.mp3", "wb") as out:
            out.write(data[inicio:fin])
        ocupados.append((inicio, fin))
        print("[✔] MP3")


# ==========================
# OGV (2 videos)
def extraer_ogv():
    with open(ARCHIVO, "rb") as f:
        data = f.read()

    pos = 0
    contador = 1

    while contador <= 2:
        ini = data.find(b"OggS", pos)
        if ini == -1:
            break

        fin = ini
        while fin < len(data):
            if data[fin:fin+4] != b"OggS":
                fin += 1
                continue

            if fin + 27 >= len(data):
                break

            segs = data[fin + 26]
            header = 27 + segs
            total = sum(data[fin+27:fin+27+segs])
            fin += header + total

            # Flag de fin de stream
            if data[fin - total - header + 5] & 0x04:
                break

        if fin - ini > 200000 and not esta_encimado(ini, fin):
            with open(f"{3 + contador}.ogv", "wb") as out:
                out.write(data[ini:fin])
            ocupados.append((ini, fin))
            print(f"[✔] OGV #{contador}")
            contador += 1

        pos = ini + 4


# ==========================
# MP4
def extraer_mp4():
    with open(ARCHIVO, "rb") as f:
        data = f.read()

    ini = data.find(b"\x00\x00\x20\x74\x79\x70")
    if ini == -1:
        return

    cortes = [b"OggS", b"\xFF\xD8\xFF", b"\x50\x4B\x03\x04"]
    fin = len(data)

    for c in cortes:
        p = data.find(c, ini + 8)
        if p != -1 and p < fin:
            fin = p

    if fin - ini > 100000 and not esta_encimado(ini, fin):
        with open("6.mp4", "wb") as out:
            out.write(data[ini:fin])
        ocupados.append((ini, fin))
        print("[✔] MP4")


# ==========================
# ZIP
def extraer_zip():
    with open(ARCHIVO, "rb") as f:
        data = f.read()

    ini = data.find(b"\x50\x4B\x03\x04")
    if ini == -1:
        return

    eocd = data.rfind(b"\x50\x4B\x05\x06")
    fin = eocd + 22 if eocd != -1 else len(data)

    if not esta_encimado(ini, fin):
        with open("7.zip", "wb") as out:
            out.write(data[ini:fin])
        ocupados.append((ini, fin))
        print("[✔] ZIP")


# ==========================
# EJECUCIÓN
extraer_jpg()
extraer_mp3()
extraer_ogv()
extraer_mp4()
extraer_zip()

print("\nExtracción COMPLETA: 7 archivos.")
