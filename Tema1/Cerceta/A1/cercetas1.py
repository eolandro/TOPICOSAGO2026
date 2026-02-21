# -- Video de Youtuve : https://youtu.be/3YQprLxVV4w?si=Gujs-WjOjGnsCNih
import os
from pathlib import Path
# --- Configuración y Constantes ---
CREDITOS = """
*** Iniciando Cercetas (Extractor Automático) ***
** Equipo:
1- Alexis Maqueda Durazno
2- Daniela Mendoza Garcia
3- PALOMA GPE RANGEL OLVERA
"""

# Firmas digitales (Números Mágicos)
MAGIC_NUMBERS = {
    b'\x49\x44\x33\x02': "mp3", b'\x49\x44\x33\x03': "mp3", b'\x49\x44\x33\x04': "mp3",
    b'\xFF\xFB\x90\x64': "mp3", b'\xFF\xFA\x92\xC4': "mp3", b'\xFF\xF3\x40\xC4': "mp3",
    b'\xFF\xF2\x48\x80': "mp3", b'\x00\x00\x00\x20\x66\x74\x79\x70': "mp4",
    b'\xFF\xD8\xFF\xE0': "jpg", b'\xFF\xD8\xFF\xDB': "jpg",
    b'\x50\x4B\x03\x04\x14\x03': "zip", b'\x1A\x45\xDF\xA3': "webm",
    b'\x4F\x67\x67\x53\x00\x02': "ogv",
}

BASE_DIR = Path('.').resolve()
ARCHIVO_ENTRADA = BASE_DIR / "cerceta.mp3"
CARPETA_SALIDA = BASE_DIR / "extraidos_cercetas"


# --- Funciones de Utilidad ---

def preparar_entorno():
    """Crea la carpeta de salida y limpia archivos previos."""
    CARPETA_SALIDA.mkdir(exist_ok=True)
    mp3_reconstruido = CARPETA_SALIDA / "audio_reconstruido.mp3"
    if mp3_reconstruido.exists():
        mp3_reconstruido.unlink()
    return mp3_reconstruido


def encontrar_siguiente_firma(datos, pos_actual):
    """Busca la posición de la próxima firma conocida para delimitar el archivo actual."""
    posiciones = [datos.find(firma, pos_actual + 1) for firma in MAGIC_NUMBERS.keys()]
    validas = [p for p in posiciones if p != -1]
    return min(validas) if validas else len(datos)


def extraer_ogv(archivo_path):
    """Lógica específica para extraer flujos OGV/Ogg."""
    PATRON_OGG = b"OggS"
    try:
        data = archivo_path.read_bytes()
        idx, stream_num = 0, 0
        while stream_num < 5:
            start = data.find(PATRON_OGG, idx)
            if start == -1: break

            # Buscar el final del stream Ogg (bit 0x04 es EOS)
            end = data.find(PATRON_OGG, start + 4)
            while end != -1:
                header = data[end:end + 27]
                if len(header) >= 6 and (header[5] & 0x04):
                    end += len(header)
                    break
                end = data.find(PATRON_OGG, end + 4)

            end = end if end != -1 else len(data)
            (CARPETA_SALIDA / f"video_oculto_{stream_num}.ogv").write_bytes(data[start:end])
            stream_num += 1
            idx = end
    except Exception as e:
        print(f"Error procesando OGV: {e}")


# --- Proceso Principal ---

def main():
    print(CREDITOS)
    if not ARCHIVO_ENTRADA.exists():
        print(f"Error: No se encuentra {ARCHIVO_ENTRADA}")
        return

    mp3_final = preparar_entorno()
    datos = ARCHIVO_ENTRADA.read_bytes()

    print(f"Analizando: {ARCHIVO_ENTRADA.name}\nGuardando en: /{CARPETA_SALIDA.name}\n" + "-" * 50)

    pos, contador = 0, 1
    while pos < len(datos):
        encontrado = False
        for firma, tipo in MAGIC_NUMBERS.items():
            if datos.startswith(firma, pos):
                sig_pos = encontrar_siguiente_firma(datos, pos)
                bloque = datos[pos:sig_pos]

                if tipo == "mp3":
                    with mp3_final.open("ab") as f:
                        f.write(bloque)
                elif tipo != "ogv":  # OGV se maneja por separado según tu lógica original
                    nombre_archivo = CARPETA_SALIDA / f"extraido_{contador}.{tipo}"
                    nombre_archivo.write_bytes(bloque)
                    contador += 1

                pos = sig_pos
                encontrado = True
                break

        if not encontrado:
            pos += 1

    print("-" * 50)
    extraer_ogv(ARCHIVO_ENTRADA)
    print(f"*** Proceso completado con éxito ***")


if __name__ == "__main__":
    main()