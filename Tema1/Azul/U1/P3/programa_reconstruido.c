#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
	FILE *archivo;
	time_t semilla;
	int i, j;
	int color;
	unsigned char paleta[6] = {0, 50, 100, 150, 200, 250}; // Colores de la paleta

	// Inicializar generador de números aleatorios
	semilla = time(NULL);
	srand((unsigned int)semilla);

	// Abrir archivo PPM
	archivo = fopen("nuevo2026.ppm", "wb");
	if (archivo == NULL)
	{
		return 1;
	}

	// Escribir encabezado PPM (P6 640 480 255)
	fprintf(archivo, "P6\n640 480\n255\n");

	// Generar imagen de 480 filas x 640 columnas
	for (i = 0; i < 480; i++)
	{ // 0x1e0 = 480
		for (j = 0; j < 640; j++)
		{ // 0x280 = 640
			// Escribir 3 componentes RGB aleatorios
			color = rand() % 6;
			fwrite(&paleta[color], 1, 1, archivo); // R

			color = rand() % 6;
			fwrite(&paleta[color], 1, 1, archivo); // G

			color = rand() % 6;
			fwrite(&paleta[color], 1, 1, archivo); // B
		}
	}

	fclose(archivo);
	return 0;
}