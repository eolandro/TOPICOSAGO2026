from collections import deque
import os
import re
import sys

# Diccionario UNIFICADO: {'tipo': (header_bytes, footer_bytes, extension)}
# Cubre todos los formatos del original Act-1.py
SIGNATURES = {
    'zip': (b'PK\x03\x04', b'PK\x05\x06', 'zip'),
    'ogg': (b'OggS', b'\x04', 'ogg'),  # Simplificado: busca 0x04 en header type
    'jpg': (b'\xFF\xD8\xFF', b'\xFF\xD9', 'jpg'),
    'mp3': (b'ID3', b'', 'mp3'),  # Sin footer fijo, usa límite
    'mp4': (b'\x00\x00\x00\x20ftyp', b'', 'mp4')  # Header ftyp, sin footer fijo
    # Agrega más: 'pdf': (b'%PDF', b'%%EOF', 'pdf')
}

def leer_archivo_binario(ruta):
    """Paso 1: Leer archivo binario completo a bytes (igual que Act-1)"""
    with open(ruta, 'rb') as f:
        return f.read()

def cola_buscadora(archivo_bytes, magic_bytes):
    """Paso 3: Buscar magic con cola deslizante (igual que Act-1, eficiente O(n))"""
    m = len(magic_bytes)
    if m == 0:
        return []
    cola = deque(maxlen=m)
    posiciones = []
    for i, byte in enumerate(archivo_bytes):
        cola.append(byte)
        if len(cola) == m and bytes(cola) == magic_bytes:
            posiciones.append(i - m + 1)
    return posiciones

def extraer_archivos_encontrados(archivo_bytes, colahits, outputdir):
    """Paso 4: Extraer/guardar con dedup y footers (lógica similar a mi primer código)"""
    os.makedirs(outputdir, exist_ok=True)
    hits = list(colahits)
    if not hits:
        return []
    
    # Ordena por inicio, dedup básico
    hits.sort(key=lambda h: h[0])
    dedup = []
    i = 0
    while i < len(hits):
        j = i + 1
        best = hits[i]
        while j < len(hits) and hits[j][0] == hits[i][0]:
            if len(hits[j][3]) > len(best[3]):  # Elige el mejor footer
                best = hits[j]
            j += 1
        dedup.append(best)
        i = j
    
    rutas = []
    for idx, (inicio, nombre, ext, magic) in enumerate(dedup, start=1):
        # Busca footer después del header
        footer = SIGNATURES[nombre][1]
        if footer:
            footer_matches = [m.start() for m in re.finditer(re.escape(footer), archivo_bytes[inicio:])]
            if footer_matches:
                fin = inicio + footer_matches[0] + len(footer)
            else:
                fin = len(archivo_bytes)  # Fallback
        else:
            fin = min(len(archivo_bytes), inicio + 1024*1024)  # Límite 1MB como Act-1
        
        if fin > inicio:
            datos = archivo_bytes[inicio:fin]
            outname = f"recovered_{idx:05d}_{nombre}_0x{inicio:08X}.{ext}"
            outpath = os.path.join(outputdir, outname)
            with open(outpath, 'wb') as f:
                f.write(datos)
            rutas.append(outpath)
            print(f"Extraído: {outname} ({len(datos)} bytes)")
    
    return rutas

def main(input_file, output_dir='ArchivosRecuperados'):
    blob = leer_archivo_binario(input_file)
    all_hits = []
    
    for file_type, (header, footer, ext) in SIGNATURES.items():
        print(f"Buscando {file_type}...")
        posiciones = cola_buscadora(blob, header)
        for pos in posiciones:
            all_hits.append((pos, file_type, ext, footer))
    
    extraer_archivos_encontrados(blob, all_hits, output_dir)
    print("¡Listo! Archivos en", output_dir)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python Act1_Simple.py <archivo.bin>")
        sys.exit(1)
    main(sys.argv[1])
