"""
Genera app/assets/fondo_combinado.jpg a partir de las tres imagenes del Congreso.
Correr una sola vez: python app/generar_fondo.py
"""

from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np

ASSETS = Path(__file__).parent / "assets"
SALIDA = ASSETS / "fondo_combinado.jpg"

ANCHO_CANVAS = 1920
ALTO_CANVAS  = 900
BLEND        = 100    # zona de fusion entre imagenes (px)
BLUR_RADIO   = 2
BRILLO       = 0.60
CALIDAD      = 88

# Proporciones visibles: costados 25% cada uno, centro 50%
# Formula: SW_lat + SW_centro + SW_lat - 2*BLEND = ANCHO_CANVAS
# => 2*SW_lat + SW_centro = ANCHO_CANVAS + 2*BLEND = 2120
SW_LATERAL = 530   # 25% visible: 530 - 50 = 480px
SW_CENTRO  = 1060  # 50% visible: 1060 - 100 = 960px
# Check: 530 + 1060 + 530 - 200 = 1920 ✓

ORDEN = [
    "congreso3.jpg",
    "congreso (1).jpg",
    "N732QHZEXRDKNADNAI7V2VHXEI (1).jpg",
]


def recortar_centro(img, ancho, alto):
    return ImageOps.fit(img.convert("RGB"), (ancho, alto), Image.LANCZOS, centering=(0.5, 0.5))


def fusionar_par(izq, der, blend):
    """Fusiona dos imagenes con degradado suave en la zona de overlap."""
    total = izq.width + der.width - blend
    canvas = Image.new("RGB", (total, izq.height))
    canvas.paste(izq, (0, 0))

    # Mask: 0 = deja pasar izq (izquierda del seam), 255 = muestra der (derecha del seam)
    mascara = np.linspace(0, 255, blend, dtype=np.uint8)
    mascara_img = Image.fromarray(
        np.tile(mascara, (izq.height, 1)).astype(np.uint8), mode="L"
    )
    # Zona de blend: primeros `blend` pixeles de `der` sobre el final de `izq`
    canvas.paste(der.crop((0, 0, blend, der.height)), (izq.width - blend, 0), mascara_img)
    # Resto de `der` sin blend
    canvas.paste(der.crop((blend, 0, der.width, der.height)), (izq.width, 0))
    return canvas


def main():
    fuentes = [ASSETS / nombre for nombre in ORDEN]

    print("Imagenes fuente (en orden):")
    for f in fuentes:
        if not f.exists():
            raise FileNotFoundError(f"No se encontro: {f}")
        print(f"  {f.name}")

    anchos = [SW_LATERAL, SW_CENTRO, SW_LATERAL]
    imgs = [
        recortar_centro(Image.open(r), ancho, ALTO_CANVAS)
        for r, ancho in zip(fuentes, anchos)
    ]

    print(f"Segmentos: {anchos[0]}px | {anchos[1]}px | {anchos[2]}px")
    print("Combinando imagenes...")
    combinada = fusionar_par(imgs[0], imgs[1], BLEND)
    combinada = fusionar_par(combinada, imgs[2], BLEND)
    combinada = combinada.crop((0, 0, ANCHO_CANVAS, ALTO_CANVAS))
    print(f"Tamano del canvas: {combinada.width} x {combinada.height} px")

    if BLUR_RADIO > 0:
        print(f"Aplicando blur (radio={BLUR_RADIO})...")
        combinada = combinada.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIO))

    print(f"Oscureciendo al {int(BRILLO * 100)} %...")
    combinada = ImageEnhance.Brightness(combinada).enhance(BRILLO)

    combinada.save(SALIDA, "JPEG", quality=CALIDAD)
    tamano_mb = SALIDA.stat().st_size / (1024 * 1024)
    print(f"\nGuardado: {SALIDA.name} ({tamano_mb:.2f} MB)")


if __name__ == "__main__":
    main()
