import os

def parcheador_inteligente():
    escritorio = r"C:\Users\Thinkpad\Desktop"
    nombre_archivo = os.path.join(escritorio, "prueba (1).exe")
    nombre_parchado = os.path.join(escritorio, "produccion_reparado.exe")
    
    patron_original = b'\x0F\x85\x13\x00\x00\x00'
    bytes_parche = b'\x90\x90\x90\x90\x90\x90'

    if not os.path.exists(nombre_archivo):
        print(f"No se encontró: {nombre_archivo}")
        return

    try:
        with open(nombre_archivo, "rb") as f:
            datos = bytearray(f.read())

        indice = datos.find(patron_original)

        if indice != -1:
            print(f"Patrón encontrado en el offset físico: {hex(indice)}")
            
            datos[indice:indice+6] = bytes_parche
            
            with open(nombre_parchado, "wb") as f:
                f.write(datos)
            
            print("SISTEMA PARCHEADO CON EXITO")
            print(f"Archivo creado: {nombre_parchado}")
        else:
            print("No se encontro el patron JNE en el archivo.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parcheador_inteligente()
