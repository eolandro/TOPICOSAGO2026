from pathlib import Path

print("*** EXTRACCIÓN FORENSE Im Blue da dira da***")

# ── Rutas ────────────────────────────────────────────────────────────────────
c = Path(r"C:\Users\leo_d\OneDrive\Documentos\TopicosCiber\Unidad1\Practica1")

archivo_azul = c / "azul"
base_dir     = c / "ANALISIS_FORENSE_AZUL"

img_jpg = base_dir / "IMAGENES_JPG"
aud_mp3 = base_dir / "AUDIO_MP3"
vid_mp4 = base_dir / "VIDEO_MP4"
vid_ogv = base_dir / "VIDEO_OGV"
zip_dir = base_dir / "COMPRIMIDOS_ZIP"

for carpeta in [img_jpg, aud_mp3, vid_mp4, vid_ogv, zip_dir]:
    carpeta.mkdir(parents=True, exist_ok=True)

# ── Lectura ──────────────────────────────────────────────────────────────────
with archivo_azul.open("rb") as f:
    datos = f.read()

print(f"[+] Archivo leído: {len(datos):,} bytes")

# ── Validadores ──────────────────────────────────────────────────────────────

def es_zip_valido(datos, pos):
    """Valida que sea un Local File Header ZIP real.
       Estructura tras PK\\x03\\x04:
         +4  version needed (2 bytes, esperamos <= 63)
         +6  flags          (2 bytes)
         +8  compression    (2 bytes, 0=store, 8=deflate, 9=deflate64)
         +14 crc32          (4 bytes)
         +26 filename_len   (2 bytes, > 0)
    """
    if pos + 30 > len(datos):
        return False
    version     = int.from_bytes(datos[pos+4 : pos+6],  'little')
    compression = int.from_bytes(datos[pos+8 : pos+10], 'little')
    fname_len   = int.from_bytes(datos[pos+26: pos+28], 'little')
    return (version <= 63
            and compression in (0, 8, 9)
            and fname_len > 0)

def es_id3_valido(datos, pos):
    if pos + 10 > len(datos):
        return False
    version    = datos[pos + 3]
    revision   = datos[pos + 4]
    size_bytes = datos[pos + 6 : pos + 10]
    return (version in (2, 3, 4)
            and revision != 0xFF
            and all(b < 0x80 for b in size_bytes))

def es_sync_mp3_valido(datos, pos):
    if pos + 4 > len(datos):
        return False
    b1, b2       = datos[pos + 1], datos[pos + 2]
    layer        = (b1 >> 1) & 0x03
    bitrate_idx  = (b2 >> 4) & 0x0F
    samplerate_i = (b2 >> 2) & 0x03
    return layer != 0 and bitrate_idx not in (0x0, 0xF) and samplerate_i != 0x03

def buscar_mp3(datos):
    pos = 0
    while (pos := datos.find(b'\x49\x44\x33', pos)) != -1:
        if es_id3_valido(datos, pos):
            print(f"    [MP3] ID3v2 válido @ offset {pos:,}")
            return pos
        else:
            print(f"    [MP3] ID3 falso positivo descartado @ offset {pos:,}")
        pos += 1
    for sync in [b'\xff\xfb', b'\xff\xfa', b'\xff\xf3', b'\xff\xf2']:
        pos = 0
        while (pos := datos.find(sync, pos)) != -1:
            if es_sync_mp3_valido(datos, pos):
                print(f"    [MP3] Sync-frame {sync.hex()} @ offset {pos:,}")
                return pos
            pos += 1
    return None

# ── OGV: agrupación por BOS ──────────────────────────────────────────────────
OGV_BOS = b'\x4f\x67\x67\x53\x00\x02'
BOS_GAP = 65_536

todos_bos = []
pos = 0
while (pos := datos.find(OGV_BOS, pos)) != -1:
    todos_bos.append(pos)
    pos += len(OGV_BOS)

print(f"\n[OGV] Total páginas BOS encontradas: {len(todos_bos)}")
for b in todos_bos:
    print(f"      BOS @ offset {b:,}")

inicios_ogv = []
if todos_bos:
    grupo_inicio = todos_bos[0]
    prev = todos_bos[0]
    for bos in todos_bos[1:]:
        if bos - prev > BOS_GAP:
            inicios_ogv.append(grupo_inicio)
            grupo_inicio = bos
        prev = bos
    inicios_ogv.append(grupo_inicio)

print(f"[OGV] Archivos OGV detectados: {len(inicios_ogv)}")
for idx, ini in enumerate(inicios_ogv, 1):
    print(f"      OGV {idx} empieza @ offset {ini:,}")

# ── Búsqueda del resto ───────────────────────────────────────────────────────
puntos = []

# JPG
for firma in [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xdb', b'\xff\xd8\xff\xee']:
    pos = 0
    jpg_encontrados = sum(1 for p in puntos if p["tipo"] == "jpg")
    while (pos := datos.find(firma, pos)) != -1 and jpg_encontrados < 2:
        puntos.append({"tipo": "jpg", "pos": pos})
        jpg_encontrados += 1
        pos += len(firma)

# MP4
pos = 0
while (pos := datos.find(b'\x66\x74\x79\x70', pos)) != -1:
    if sum(1 for p in puntos if p["tipo"] == "mp4") < 1:
        puntos.append({"tipo": "mp4", "pos": pos - 4})
    pos += 4

# ZIP — con validación, busca el primero válido
pos = 0
zip_encontrado = False
while (pos := datos.find(b'\x50\x4b\x03\x04', pos)) != -1:
    if es_zip_valido(datos, pos):
        print(f"    [ZIP] Local File Header válido @ offset {pos:,}")
        puntos.append({"tipo": "zip", "pos": pos})
        zip_encontrado = True
        break
    else:
        print(f"    [ZIP] Falso positivo descartado @ offset {pos:,}")
    pos += 4

if not zip_encontrado:
    print("[!] ADVERTENCIA: no se encontró ningún ZIP válido")

# OGV
for ini in inicios_ogv[:2]:
    puntos.append({"tipo": "ogv", "pos": ini})

# MP3
mp3_offset = buscar_mp3(datos)
if mp3_offset is not None:
    puntos.append({"tipo": "mp3", "pos": mp3_offset})
else:
    print("[!] ADVERTENCIA: no se encontró ningún MP3 válido")

puntos.sort(key=lambda x: x["pos"])

print(f"\n[+] Puntos de extracción ordenados:")
for p in puntos:
    print(f"    {p['tipo']:>3}  @ offset {p['pos']:,}")

# ── Extracción ───────────────────────────────────────────────────────────────
jpg_n = 0
ogv_n = 0

for i, p in enumerate(puntos):
    inicio = p["pos"]
    tipo   = p["tipo"]
    fin    = puntos[i + 1]["pos"] if i + 1 < len(puntos) else len(datos)

    if tipo == "jpg":
        jpg_n += 1
        nombre = img_jpg / f"jpg{jpg_n}.jpg"

    elif tipo == "mp3":
        if (fin - inicio) < 2_000_000:
            fin = inicio + 12_000_000
        nombre = aud_mp3 / "mp31.mp3"

    elif tipo == "mp4":
        if (fin - inicio) < 5_000_000:
            fin = inicio + 15_000_000
        nombre = vid_mp4 / "mp4.mp4"

    elif tipo == "ogv":
        if (fin - inicio) < 5_000_000:
            fin = inicio + 5_000_000
        ogv_n += 1
        nombre = vid_ogv / ("ogv1.ogv" if ogv_n == 1 else "ogv2.ogv")

    elif tipo == "zip":
        nombre = zip_dir / "zip.zip"

    fin = min(fin, len(datos))

    with nombre.open("wb") as out:
        out.write(datos[inicio:fin])

    size_mb = (fin - inicio) / 1_048_576
    print(f"[+] Extraído: {nombre.name}  ({size_mb:.1f} MB)")


print("\n--- Proceso finalizado con éxito Lo logreeeeee carajo Leo estuvo aquí---")