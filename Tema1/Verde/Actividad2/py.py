from pathlib import Path

DespOriginal = 0x248  # posición inicial
ArchivoOriginal = "prueba.exe"
ArchivoModificado = "elCrack.exe"

cwd = Path('.').resolve()
ArchioCrack = cwd / ArchivoOriginal
ArchivoCrackeado = cwd / ArchivoModificado

if __name__ == '__main__':
    binario = None

    if ArchioCrack.exists():
        with ArchioCrack.open('rb') as secbytes:
            
            binario = secbytes.read(DespOriginal)

           
            originales = secbytes.read(6)
            print("Bytes que se cambiarán:", originales.hex())

            
            binario = binario + b'\x74\x17\x90\x90\x90\x90'

           
            binario = binario + secbytes.read()

        crk = ArchivoCrackeado.open("wb")
        crk.write(binario)
        crk.close()

        print(f"Su parche fue aplicado, ejecute {ArchivoCrackeado}")

    else:
        print("El archivo no existe")
