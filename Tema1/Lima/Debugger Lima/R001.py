from pathlib import Path

print("*** EXTRACCIÓN FORENSE ***")

c = Path("/mnt/c/Users/Thinkpad/Desktop")

archivo_lima = c / "lima"
base_dir = c / "ANALISIS_FORENSE_LIMA"

img_jpg = base_dir / "IMAGENES_JPG"
aud_mp3 = base_dir / "AUDIO_MP3"
vid_mp4 = base_dir / "VIDEO_MP4"
vid_ogv = base_dir / "VIDEO_OGV"
zip_dir = base_dir / "COMPRIMIDOS_ZIP"

img_jpg.mkdir(parents=True, exist_ok=True)
aud_mp3.mkdir(parents=True, exist_ok=True)
vid_mp4.mkdir(parents=True, exist_ok=True)
vid_ogv.mkdir(parents=True, exist_ok=True)
zip_dir.mkdir(parents=True, exist_ok=True)

U = archivo_lima.open("rb")
datos = U.read()
U.close()

print(f"[+] Archivo leído: {len(datos)} bytes")

firmas = [
    ("jpg", b'\xff\xd8\xff\xe0'),
    ("jpg", b'\xff\xd8\xff\xdb'),
    ("jpg", b'\xff\xd8\xff\xee'),
    ("mp3", b'\x49\x44\x33'),
    ("mp4", b'\x66\x74\x79\x70'),
    ("ogv", b'\x4f\x67\x67\x53'),
    ("zip", b'\x50\x4b\x03\x04')
]

limite = {
    "jpg": 2,
    "mp3": 1,
    "ogv": 2,
    "mp4": 1,
    "zip": 1
}

contados = {k: 0 for k in limite}
puntos = []

for tipo, firma in firmas:
    pos = 0
    while (pos := datos.find(firma, pos)) != -1:
        if contados[tipo] < limite[tipo]:
            pos_real = pos - 4 if tipo == "mp4" else pos
            puntos.append({"tipo": tipo, "pos": pos_real})
            contados[tipo] += 1
        pos += 5_000_000 if tipo in ["mp3", "ogv"] else len(firma)

puntos.sort(key=lambda x: x["pos"])

jpg_n = 0
ogv_n = 0

for i, p in enumerate(puntos):
    inicio = p["pos"]
    tipo = p["tipo"]
    fin = puntos[i + 1]["pos"] if i + 1 < len(puntos) else len(datos)

    if tipo == "jpg":
        footer = datos.find(b'\xff\xd9', inicio)
        if footer != -1:
            fin = footer + 2

        jpg_n += 1
        nombre = img_jpg / f"jpg{jpg_n}.jpg"

    elif tipo == "mp3":
        if (fin - inicio) < 2_000_000:
            fin = inicio + 12_000_000
        nombre = aud_mp3 / "mp31.mp3"

    elif tipo == "ogv":
        fin = inicio + 12_000_000
        ogv_n += 1
        nombre = vid_ogv / ("ogv.ogv" if ogv_n == 1 else "2.ogv")

    elif tipo == "mp4":
        if (fin - inicio) < 5_000_000:
            fin = inicio + 15_000_000
        nombre = vid_mp4 / "mp4.mp4"

    elif tipo == "zip":
        footer = datos.find(b'\x50\x4b\x05\x06', inicio)
        if footer != -1:
            fin = footer + 22
        nombre = zip_dir / "zip.zip"

    if fin > len(datos):
        fin = len(datos)

    V = nombre.open("wb")
    V.write(datos[inicio:fin])
    V.close()

# Aplicamos este parche porque el segundo OGV no tenia una cabecera valida y era necesario reconstruirla para que pudiera reproducirse
ogv1 = vid_ogv / "ogv.ogv"
ogv2 = vid_ogv / "2.ogv"

if ogv1.exists() and ogv2.exists():
    cabecera = ogv1.open("rb").read(65536)
    cuerpo = ogv2.open("rb").read()
    V = ogv2.open("wb")
    V.write(cabecera + cuerpo)
    V.close()

print("\n--- Proceso finalizado con éxito ---")
