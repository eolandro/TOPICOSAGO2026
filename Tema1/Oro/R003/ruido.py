#!/usr/bin/env python3  
import argparse
import ctypes
import time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="nuevo2026.ppm")
    ap.add_argument("--seed", type=int, default=None,
                    help="usa int(time.time()) (segundos).")
    args = ap.parse_args()

    # MSVCRT (Windows)
    msvcrt = ctypes.CDLL("msvcrt")
    msvcrt.srand.argtypes = [ctypes.c_uint]
    msvcrt.rand.restype = ctypes.c_int

    seed = args.seed if args.seed is not None else int(time.time())
    seed &= 0xFFFFFFFF
    msvcrt.srand(seed)

    header = b"P6\n640 480\n255\n"  # 15 bytes
    pal = bytes([0x32, 0x64, 0x96, 0xC8, 0xFA, 0xE6])  

    with open(args.out, "wb") as f:
        f.write(header)
        for _y in range(480):
            for _x in range(640):
                f.write(bytes([pal[msvcrt.rand() % 6],
                               pal[msvcrt.rand() % 6],
                               pal[msvcrt.rand() % 6]]))

    print(f"OK: {args.out} generado con seed={seed}")

if __name__ == "__main__":
    main()                              
