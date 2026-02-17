from pathlib import Path

Desp = 0x210+2 # Este es la posicion donde se debe modificar el byte

Ejecutable = "prueba.exe"
EjecutableCrack = 'ejemplo_patch.exe'
cwd = Path('.').resolve()
ArchivoCrack = cwd / Ejecutable
ArchivoCrackeado = cwd / EjecutableCrack

if __name__ == '__main__':
    binario = None
    if ArchivoCrack.exists():
        with ArchivoCrack.open('rb') as secbytes:
            binario = secbytes.read(Desp) # leo todos los bytes previos al que se necesita cambiar
            print(f"Se cambiara {secbytes.read(1)} por (b'\\x00')") #imprimo el byte que sera cambiado
            binario = binario + b'\x00'
            binario = binario + secbytes.read()
            crk = ArchivoCrackeado.open('wb')
            crk.write(binario)
            crk.close()
            print(f"Su parche fue aplicado ejecute {ArchivoCrackeado}")
    else:
        print("No se encontro el archivo a parchar")
