#!/usr/bin/env python3

import argparse              # Para leer argumentos de consola
import hashlib               
import json                  # Para generar report.json
#Chat me recomendo el jason para identificar porque no jala el ogv pero no logre arreglarlo
import os                    
import struct                # Para desempaquetar enteros binarios (MP4/ZIP/OGG) lo tuve que buscar


# ============================================================
# UTILIDADES BÁSICAS
# ============================================================

def calcular_tamaño(bytes_totales: int) -> str:
    """
    Convierte bytes a string : 123B, 10KB, 55MB, etc.
    """
    valor = float(bytes_totales)
    for unidad in ["B", "KB", "MB", "GB", "TB"]:
        if valor < 1024:
            return f"{valor:.0f}{unidad}"
        valor /= 1024
    return f"{valor:.0f}PB"


def leer_en(archivo, desplazamiento: int, cantidad: int) -> bytes:
    """
    Lee cuantos bytes desde 'desplazamiento' en un archivo ya abierto.
    """
    archivo.seek(desplazamiento)
    return archivo.read(cantidad)


def asegurar_directorio(ruta_directorio: str) -> None:
    """
    Crea la carpeta  si no existe.
    """
    os.makedirs(ruta_directorio, exist_ok=True)


def tamano_bloque_a_bytes(texto: str) -> int:
    """
    Convierte una entrada como:
      "16M" -> 16 * 1024^2
      "8K"  -> 8 * 1024
      "1G"  -> 1 * 1024^3
      "123" -> 123
    """
    texto = texto.strip().upper()
    if not texto:
        raise ValueError("tamaño de bloque vacío")

    sufijo = texto[-1]
    parte_numerica = texto[:-1]

    if sufijo == "K":
        return int(parte_numerica) * 1024
    if sufijo == "M":
        return int(parte_numerica) * 1024 * 1024
    if sufijo == "G":
        return int(parte_numerica) * 1024 * 1024 * 1024

    return int(texto)


def mp4_ascii(byte_mp4: bytes) -> bool:
    """
    MP4 suelen ser 4 chars ASCII imprimibles.
    """
    return len(byte_mp4) == 4 and all(0x20 <= b <= 0x7E for b in byte_mp4)


# ============================================================
# (ENCONTRAR FIN POR TIPO)
# ============================================================
#A este no le muevan que al principio me extraia 700 jpg y no se como lo hice jalar XD, chat tampcoo fue de mucha ayuda
def buscar_fin_jpg(archivo, inicio: int, tamano_total: int, tamano_escaneo: int = 8 * 1024 * 1024) -> int | None:
    """
    Carver para JPG: encuentra el marcador EOI: FF D9.
    """
    posicion = inicio + 3
    solape = b""
    #solape es pra que no se solapen o encimen los bytes repetidos

    while posicion < tamano_total:
        archivo.seek(posicion)
        bloque = archivo.read(tamano_escaneo)
        if not bloque:
            break

        datos = solape + bloque
        indice = datos.find(b"\xff\xd9")

        if indice != -1:
            return (posicion - len(solape)) + indice + 2

        solape = datos[-1:]
        posicion += len(bloque)

    return None

#Chequenle a esta madre que no me quedan estos archivos
def buscar_fin_ogg(archivo, inicio: int, tamano_total: int, max_paginas: int = 2_000_000) -> int | None:
    """
    Carver para OGG/OGV:
    - Recorre páginas OggS.
    - Termina cuando encuentra flag EOS o cuando falla.
    """
    posicion = inicio
    paginas_leidas = 0
    serial_esperado = None

    while posicion + 27 <= tamano_total and paginas_leidas < max_paginas:
        encabezado = leer_en(archivo, posicion, 27)
        if len(encabezado) < 27 or encabezado[:4] != b"OggS":
            return None if paginas_leidas == 0 else posicion

        if encabezado[4] != 0:
            return None if paginas_leidas == 0 else posicion

        banderas = encabezado[5]
        cantidad_segmentos = encabezado[26]
        tabla_segmentos = leer_en(archivo, posicion + 27, cantidad_segmentos)
        if len(tabla_segmentos) != cantidad_segmentos:
            return None if paginas_leidas == 0 else posicion

        longitud_cuerpo = sum(tabla_segmentos)
        serial = struct.unpack("<I", encabezado[14:18])[0]

        if serial_esperado is None:
            serial_esperado = serial

        if serial != serial_esperado and paginas_leidas < 5:
            return None

        posicion = posicion + 27 + cantidad_segmentos + longitud_cuerpo
        paginas_leidas += 1

        if banderas & 0x04:
            return posicion

    return None


def buscar_fin_zip(archivo, inicio: int, tamano_total: int, tamano_escaneo: int = 8 * 1024 * 1024) -> int | None:
    """
    Carver para ZIP:
    - Busca el EOCD: "PK 05 06".
    - Valida tamaño mínimo y longitud del comentario.
    si ven por ahi CARVER es de cavar pero lo escribi mal y ya lo deje asi, pero es el que encuentra el inicio de los archivos 
    """
    FIRMA_EOCD = b"PK\x05\x06"
    posicion = inicio
    solape = b""

    while posicion < tamano_total:
        archivo.seek(posicion)
        bloque = archivo.read(tamano_escaneo)
        if not bloque:
            break

        datos = solape + bloque
        base_real = posicion - len(solape)

        indice = datos.find(FIRMA_EOCD)
        while indice != -1:
            offset_eocd = base_real + indice

            if offset_eocd + 22 <= tamano_total:
                eocd_min = leer_en(archivo, offset_eocd, 22)
                if len(eocd_min) == 22 and eocd_min[:4] == FIRMA_EOCD:
                    longitud_comentario = struct.unpack("<H", eocd_min[20:22])[0]
                    fin = offset_eocd + 22 + longitud_comentario

                    if fin <= tamano_total:
                        disco_actual, disco_central = struct.unpack("<HH", eocd_min[4:8])
                        if disco_actual == disco_central:
                            return fin

            indice = datos.find(FIRMA_EOCD, indice + 1)

        solape = datos[-4:]
        posicion += len(bloque)

    return None


# ----------------------------
# MP3 
# ----------------------------
#Este lo encontre en el stack

# Tablas MP3: bitrate y samplerate 
TASAS_BITS = {
    (1, 1): [0,32,64,96,128,160,192,224,256,288,320,352,384,416,448,0],
    (1, 2): [0,32,48,56,64,80,96,112,128,160,192,224,256,320,384,0],
    (1, 3): [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0],
    (2, 1): [0,32,48,56,64,80,96,112,128,144,160,176,192,224,256,0],
    (2, 2): [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0],
    (2, 3): [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0],
}

FRECUENCIAS_MUESTREO = {
    1:  [44100, 48000, 32000, 0],             # MPEG1
    2:  [22050, 24000, 16000, 0],             # MPEG2
    25: [11025, 12000, 8000, 0],              # MPEG2.5
}

def synchsafe_a_entero(b4: bytes) -> int:
    """
    ID3v2 usa “synchsafe”: 4 bytes con 7 bits útiles cada uno.
    """
    return ((b4[0] & 0x7F) << 21) | ((b4[1] & 0x7F) << 14) | ((b4[2] & 0x7F) << 7) | (b4[3] & 0x7F)


def longitud_frame_mp3_desde_header(header4: bytes) -> int | None:
    """
    Intenta parsear un header de frame MP3 y regresa la longitud del frame.
    """
    if len(header4) != 4:
        return None

    b1, b2, b3, b4 = header4

    if b1 != 0xFF or (b2 & 0xE0) != 0xE0:
        return None

    id_version = (b2 >> 3) & 0x03
    id_layer = (b2 >> 1) & 0x03

    if id_version == 1 or id_layer == 0:
        return None

    if id_version == 3:
        version_mpeg = 1
    elif id_version == 2:
        version_mpeg = 2
    elif id_version == 0:
        version_mpeg = 25
    else:
        return None

    layer = {3: 1, 2: 2, 1: 3}[id_layer]

    idx_bitrate = (b3 >> 4) & 0x0F
    idx_muestreo = (b3 >> 2) & 0x03
    padding = (b3 >> 1) & 0x01

    if idx_muestreo == 3:
        return None

    frecuencia = FRECUENCIAS_MUESTREO[version_mpeg][idx_muestreo]
    if frecuencia == 0:
        return None

    clave_tabla = 1 if version_mpeg == 1 else 2
    bitrate = TASAS_BITS.get((clave_tabla, layer), [0] * 16)[idx_bitrate]
    if bitrate == 0:
        return None

    if layer == 1:
        longitud = int((12 * bitrate * 1000 / frecuencia + padding) * 4)
    else:
        coeficiente = 144000 if (version_mpeg == 1 or layer == 2) else 72000
        longitud = int(coeficiente * bitrate / frecuencia + padding)

    if longitud < 24 or longitud > 10_000:
        return None

    return longitud


def buscar_fin_mp3(archivo, inicio: int, tamano_total: int, min_frames_validos: int = 10) -> int | None:
    """
    Carver MP3:
    - Si hay ID3v2 al inicio, lo salta.
    - Luego avanza frame por frame.
    """
    posicion = inicio

    encabezado = leer_en(archivo, posicion, 10)
    if len(encabezado) == 10 and encabezado[:3] == b"ID3":
        tam_tag = synchsafe_a_entero(encabezado[6:10])
        posicion = posicion + 10 + tam_tag
        if posicion >= tamano_total:
            return None

    frames_ok = 0
    fallos_consecutivos = 0
    ultimo_bueno = posicion

    while posicion + 4 <= tamano_total:
        longitud = longitud_frame_mp3_desde_header(leer_en(archivo, posicion, 4))

        if longitud is None:
            fallos_consecutivos += 1
            if fallos_consecutivos >= 3:
                break
            posicion += 1
            continue

        fallos_consecutivos = 0
        siguiente = posicion + longitud
        if siguiente > tamano_total:
            break

        ultimo_bueno = siguiente
        posicion = siguiente
        frames_ok += 1

    return ultimo_bueno if frames_ok >= min_frames_validos else None

#Recicle el que encontre pal mp3 XD
def buscar_fin_mp4(archivo, inicio: int, tamano_total: int, max_cajas: int = 1_000_000) -> int | None:
    """
    - Debe iniciar con box 'ftyp'.
    - Recorre boxes validando tamaños.
    """
    posicion = inicio
    if posicion + 8 > tamano_total:
        return None

    tipo_inicial = leer_en(archivo, posicion + 4, 4)
    if tipo_inicial != b"ftyp":
        return None

    vio_moov = False
    # el moov lo encontre en internet, es el inicio
    vio_mdat = False
    # este es como el contendio
    vio_moof = False
    #no entendi bien que es este pero creo que es el moov y el mdat pero fragmentados
    ultimo_bueno = posicion
    cajas = 0

    while posicion + 8 <= tamano_total and cajas < max_cajas:
        header = leer_en(archivo, posicion, 8)
        if len(header) < 8:
            break

        tam_caja = struct.unpack(">I", header[:4])[0]
        byte_mp4 = header[4:8]
        longitud_header = 8

        if not mp4_ascii(byte_mp4):
            break

        if tam_caja == 0:
            ultimo_bueno = tamano_total
            break

        if tam_caja == 1:
            extendido = leer_en(archivo, posicion + 8, 8)
            if len(extendido) < 8:
                break
            tam_caja = struct.unpack(">Q", extendido)[0]
            longitud_header = 16

        if tam_caja < longitud_header:
            break

        siguiente = posicion + tam_caja
        if siguiente > tamano_total:
            break

        if byte_mp4 == b"moov":
            vio_moov = True
        elif byte_mp4 == b"mdat":
            vio_mdat = True
        elif byte_mp4 == b"moof":
            vio_moof = True

        ultimo_bueno = siguiente
        posicion = siguiente
        cajas += 1

    if (vio_mdat and (vio_moov or vio_moof)) or vio_moov:
        return ultimo_bueno

    return None


def fin_por_tipo(archivo, tipo: str, inicio: int, tamano_total: int) -> int | None:
    """
    “Router” por tipo: llama al carver correspondiente.
    """
    if tipo == "jpg":
        return buscar_fin_jpg(archivo, inicio, tamano_total)
    if tipo == "ogv":
        return buscar_fin_ogg(archivo, inicio, tamano_total)
    if tipo == "zip":
        return buscar_fin_zip(archivo, inicio, tamano_total)
    if tipo == "mp3":
        return buscar_fin_mp3(archivo, inicio, tamano_total)
    if tipo == "mp4":
        return buscar_fin_mp4(archivo, inicio, tamano_total)
    return None


# ============================================================
# ESCANEO DE FIRMAS (MAGIC NUMBERS)
# ============================================================

def escanear_firmas(ruta_archivo: str, tamano_chunk: int, solape: int):
    """
    Escanea el archivo y busca firmas .
    con este evito que salgan archivos falsos, pero creo que daña alos ogv luego lo checo
    """
    encontrados = set()

    with open(ruta_archivo, "rb") as archivo:
        offset_global = 0
        buffer_solape = b""

        while True:
            chunk = archivo.read(tamano_chunk)
            if not chunk:
                break

            datos = buffer_solape + chunk
            base_real = offset_global - len(buffer_solape)

            # 1) JPG: FF D8 FF
            firma = b"\xff\xd8\xff"
            i = datos.find(firma)
            while i != -1:
                encontrados.add(("jpg", base_real + i))
                i = datos.find(firma, i + 1)

            # 2) OGG: OggS
            firma = b"OggS"
            i = datos.find(firma)
            while i != -1:
                encontrados.add(("ogv", base_real + i))
                i = datos.find(firma, i + 1)

            # 3) ZIP: PK 03 04
            firma = b"PK\x03\x04"
            i = datos.find(firma)
            while i != -1:
                encontrados.add(("zip", base_real + i))
                i = datos.find(firma, i + 1)

            # 4) MP3: ID3
            firma = b"ID3"
            i = datos.find(firma)
            while i != -1:
                encontrados.add(("mp3", base_real + i))
                i = datos.find(firma, i + 1)

            # 5) MP4: "ftyp" (restamos 4 bytes del size)
            firma = b"ftyp"
            i = datos.find(firma)
            while i != -1:
                if i >= 4:
                    tam_guess = struct.unpack(">I", datos[i - 4:i])[0]
                    if 8 <= tam_guess <= 1_000_000:
                        encontrados.add(("mp4", base_real + i - 4))
                i = datos.find(firma, i + 1)

            # 6) MP3 sync heurístico
            j = datos.find(b"\xff")
            while j != -1 and j + 1 < len(datos):
                if (datos[j + 1] & 0xE0) == 0xE0:
                    encontrados.add(("mp3", base_real + j))
                j = datos.find(b"\xff", j + 1)

            buffer_solape = datos[-solape:] if len(datos) >= solape else datos
            offset_global += len(chunk)

    return sorted(encontrados, key=lambda x: (x[1], x[0]))


# ============================================================
# EXTRACCIÓN + SHA256
# ============================================================

def extraer_y_sha256(ruta_fuente: str, inicio: int, fin: int, ruta_salida: str, buffer: int = 8 * 1024 * 1024) -> str:
    """
    Extrae el rango [inicio, fin) y calcula SHA256.
    """
    calculador = hashlib.sha256()

    with open(ruta_fuente, "rb") as origen, open(ruta_salida, "wb") as destino:
        origen.seek(inicio)
        restante = fin - inicio

        while restante > 0:
            a_leer = min(buffer, restante)
            bloque = origen.read(a_leer)
            if not bloque:
                break
            destino.write(bloque)
            calculador.update(bloque)
            restante -= len(bloque)

    return calculador.hexdigest()


# ============================================================
# GUI SELECCIONAR ARCHIVO 
# ============================================================

def elegir_archivo_gui() -> str:
    """
    Abre un explorador de archivos, 
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        raiz = tk.Tk()
        raiz.withdraw()
        raiz.update()
        ruta = filedialog.askopenfilename(
            title="Selecciona el archivo gigante",
            filetypes=[("Todos", "*.*")]
        )
        raiz.destroy()
        return ruta or ""
    except Exception:
        return ""


# ============================================================
# MAIN
# ============================================================

def Main():
    """
    1) Seleccionamos archivo.
    2) Escanear firmas => candidatos
    3) Validar fin por tipo, extraer, hash, reporte
    4) Escribir report.json
    """
    parser = argparse.ArgumentParser(
        description="Carver simple (JPG/OGV/ZIP/MP3/MP4) por firmas + parsing."
    )

    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Archivo a analizar (si no, abre explorador)"
    )

    parser.add_argument(
        "-o", "--outdir",
        default="extracted",
        help="Carpeta de salida"
    )

    parser.add_argument(
        "--chunk",
        default="16M",
        help="Chunk de escaneo (8M/16M/32M...)"
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=1024,
        help="Overlap en bytes"
    )

    argumentos = parser.parse_args()

    ruta_entrada = argumentos.input
    if not ruta_entrada:
        ruta_entrada = elegir_archivo_gui()
        if not ruta_entrada:
            print("[-] No seleccionaste archivo.")
            return

    asegurar_directorio(argumentos.outdir)
    tamano_total = os.path.getsize(ruta_entrada)

    tamano_chunk = tamano_bloque_a_bytes(argumentos.chunk)

    print(f"[+] Entrada: {ruta_entrada} ({calcular_tamaño(tamano_total)})")
    print(f"[+] Escaneo: chunk={calcular_tamaño(tamano_chunk)}, overlap={argumentos.overlap}B")

    candidatos = escanear_firmas(ruta_entrada, tamano_chunk, argumentos.overlap)
    print(f"[+] Candidatos: {len(candidatos)}")

    conteos_por_tipo = {"jpg": 0, "ogv": 0, "zip": 0, "mp3": 0, "mp4": 0}
    lista_extraidos = []
    ocupado_hasta = -1

    with open(ruta_entrada, "rb") as archivo:
        for tipo, inicio in candidatos:
            if inicio < ocupado_hasta:
                continue

            fin = fin_por_tipo(archivo, tipo, inicio, tamano_total)

            if fin is None or fin <= inicio:
                continue

            conteos_por_tipo[tipo] += 1
            consecutivo = conteos_por_tipo[tipo]

            longitud = fin - inicio

            nombre_salida = f"{tipo}_{consecutivo:02d}_off_{inicio:08X}_len_{longitud}.{tipo}"
            ruta_salida = os.path.join(argumentos.outdir, nombre_salida)

            sha = extraer_y_sha256(ruta_entrada, inicio, fin, ruta_salida)

            ocupado_hasta = fin

            lista_extraidos.append({
                "type": tipo,
                "index": consecutivo,
                "start": inicio,
                "end": fin,
                "length": longitud,
                "sha256": sha,
                "outfile": nombre_salida
            })

            print(f"[+] EXTRAER {tipo.upper()} #{consecutivo} off=0x{inicio:X} size={calcular_tamaño(longitud)} -> {nombre_salida}")

    ruta_reporte = os.path.join(argumentos.outdir, "report.json")
    with open(ruta_reporte, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "input": os.path.basename(ruta_entrada),
                "input_size": tamano_total,
                "extracted": lista_extraidos,
                "counts": conteos_por_tipo
            },
            fp,
            indent=2,
            ensure_ascii=False
        )

    print(f"[+] Reporte: {ruta_reporte}")
    print(f"[+] Conteos: {conteos_por_tipo}")


if __name__ == "__main__":
    Main()
