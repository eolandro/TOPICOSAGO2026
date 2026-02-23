from pathlib import Path

posicion = 0x248    # Lugar exacto donde comienza la instrucción
archivo_original = "prueba.exe"
archivo_parchado = "prueba_parche.exe"

carpeta = Path(__file__).parent               
ruta_original = carpeta / archivo_original
ruta_parchado = carpeta / archivo_parchado

if not ruta_original.exists():
    print("\nNo se encuentra el archivo", archivo_original)
    exit()

with open(ruta_original, "rb") as archivo:
    datos = bytearray(archivo.read())      

if posicion + 1 >= len(datos):
    print("\nLa posición está más allá del final del archivo.")
    exit()

primer_byte = datos[posicion]            
segundo_byte = datos[posicion + 1]        # Debería ser 0x85 (JNE)

# ---- APLICAR EL PARCHE (JNE -> JE) -> cambiar el segundo byte: 0x85 -> 0x84
datos[posicion + 1] = 0x84

with open(ruta_parchado, "wb") as archivo:
    archivo.write(datos)

print("\nParche aplicado")
print(f"\nArchivo guardado en: {ruta_parchado}")
