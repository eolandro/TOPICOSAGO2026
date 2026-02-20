#EQUIPO NARANJA
https://drive.google.com/file/d/1Cc-Hps2XK9KRzLgzlRw6pDgyatDHI4Jr/view?usp=drive_link

parches = {
    0x249: 0x84
}

INPUT = "prueba_1.exe"
OUTPUT = "prueba1_parcheado.exe"

try:
    with open(INPUT, "rb") as f:
        buf = f.read()
except FileNotFoundError:
    exit()

cbt = -1
with open(OUTPUT, "wb") as salida:
    for bt in buf:
        cbt += 1
        if cbt in parches:
            bt = parches[cbt]
        salida.write(bt.to_bytes(1, 'little'))

print(f"{INPUT} ha sido parchado con éxito -> {OUTPUT}")

