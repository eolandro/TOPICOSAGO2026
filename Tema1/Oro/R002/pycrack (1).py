from pathlib import Path

DespOriginal = 0x248  
ArchivoOriginal = "prueba.exe"
ArchivoModificado = "pruebapycrack.exe"

cwd = Path('.').resolve()
ArchivoCrack = cwd / ArchivoOriginal
ArchivoCrackeado = cwd / ArchivoModificado

if __name__ == '__main__':
    binario = None

    if ArchivoCrack.exists():
        with ArchivoCrack.open('rb') as secbytes:
            
            binario = secbytes.read(DespOriginal)
           
            originales = secbytes.read(6)
            print("Bytes a modificar:", originales.hex())

            binario = binario + b'\x74\x17\x90\x90\x90\x90'
           
            binario = binario + secbytes.read()

        crk = ArchivoCrackeado.open("wb")
        crk.write(binario)
        crk.close()

        print(f"Su parche fue aplicado correctamente> {ArchivoCrackeado}")

    else:
        print("El archivo no existe")
