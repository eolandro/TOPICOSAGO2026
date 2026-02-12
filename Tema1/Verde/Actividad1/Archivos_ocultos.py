#https://youtu.be/e-qSJJTYg_o

from pathlib import Path

def busqueda():

    l=0
    b=0
    e=0

    encontrados=[]
    encontrados2=[]
    busquedaEncabezados=[['ff','d8','ff','e0'],
            ['49','44','33','02'],
            ['4f','67','67','53'],
            ['50','4b','03','04'],
            ['00','00','00','20','66','74','79','70']
            ]
    inicio=0
    final=0

    with open("verde", "rb") as f:
        while True:
            if b<=3:
                byte=f.read(1).hex()
                if not byte:
                    break
                encontrados.append(byte)
            
                if len(encontrados)==4:
                    if encontrados==busquedaEncabezados[b]:
                        final=l-4
                        convertir(e,inicio,final)
                        inicio=l-3
                        #print(b," ",e)
                        b+=1
                        e+=1
                        
                        encontrados.pop(0)    
                    else:
                        encontrados.pop(0)
                #print(l)
                l+=1

            else:
                byte=f.read(1).hex()
                encontrados2.append(byte)
                if not byte:
                    convertir(e,inicio,final)
                    break
                if len(encontrados2)==8:
                    if encontrados2==busquedaEncabezados[b]:
                        final=l-8
                        convertir(e,inicio,final)
                        inicio=l-7
                        b+=1
                        e+=1
                        #encontrados2.pop(0)    
                    else:
                        encontrados2.pop(0)
                l+=1



def convertir(b,inicio,final):
    extensiones=['.jpg','.mp3','.ogv','.zip','.mp4']
    with open("verde", "rb") as f2:
        if b==0:
            archivo = Path(f'archivo{b+1}{extensiones[0]}')
            f2.seek(0)
            hexadecimales=f2.read(final)
            print(f"!Archivo {extensiones[0]} encontrado!. Se creó archivo{b+1}{extensiones[0]}")
        else:
            archivo = Path(f'archivo{b+1}{extensiones[b-1]}')
            f2.seek(inicio)
            hexadecimales=f2.read(final-inicio)
            print(f"!Archivo {extensiones[b-1]} encontrado!. Se creó archivo{b+1}{extensiones[b-1]}")
        with archivo.open("wb") as V:
            V.write(hexadecimales)
        
        
    f2.close()

print("\t\t\t\nBuscando archivos...\n")
busqueda()
print("\t\t\t\nSe encontraron todos los archivos")



