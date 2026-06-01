from pathlib import Path

# Configuración de rutas
OFFSET = 0x248
ARCHIVO_ORIGEN = "prueba.exe"
ARCHIVO_DESTINO = "Parche.exe"
PARCHE = b'\x74\x17\x90\x90\x90\x90'

def aplicar_parche():
    ruta_base = Path('.').resolve()
    archivo_origen = ruta_base / ARCHIVO_ORIGEN
    archivo_destino = ruta_base / ARCHIVO_DESTINO

    if not archivo_origen.exists():
        print(f"Error: No se encontró el archivo '{ARCHIVO_ORIGEN}'")
        return

    try:
        with archivo_origen.open('rb') as f_in:
            # Leer hasta la posición del offset
            contenido_inicial = f_in.read(OFFSET)
            
            # Leer y mostrar los bytes que serán reemplazados
            bytes_originales = f_in.read(len(PARCHE))
            print(f"Bytes originales a reemplazar: {bytes_originales.hex()}")
            
            # Leer el resto del archivo
            resto_archivo = f_in.read()

        # Construir el nuevo binario
        binario_modificado = contenido_inicial + PARCHE + resto_archivo

        # Escribir el nuevo ejecutable
        with archivo_destino.open('wb') as f_out:
            f_out.write(binario_modificado)
        
        print(f"Parche Aplicado con éxito. Ejecute: {ARCHIVO_DESTINO}")

    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo: {e}")

if __name__ == '__main__':
    aplicar_parche()