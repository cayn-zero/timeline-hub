from io import BytesIO

import pytest
from PIL import Image

from timeline_hub.infra.images import to_jpg


def test_to_jpg_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match='image_bytes must not be empty'):
        to_jpg(b'')


def test_to_jpg_rejects_invalid_quality() -> None:
    with pytest.raises(ValueError, match='quality must be in 1..100'):
        to_jpg(b'image-bytes', quality=0)


def test_to_jpg_converts_png_to_jpeg() -> None:
    png_bytes = _build_png_bytes(mode='RGB')

    jpg_bytes = to_jpg(png_bytes)

    assert jpg_bytes
    with Image.open(BytesIO(jpg_bytes)) as image:
        image.load()
        assert image.format == 'JPEG'


def test_to_jpg_handles_transparency() -> None:
    png_bytes = _build_png_bytes(mode='RGBA')

    jpg_bytes = to_jpg(png_bytes)

    assert jpg_bytes
    with Image.open(BytesIO(jpg_bytes)) as image:
        image.load()
        assert image.format == 'JPEG'
        assert image.mode == 'RGB'


def test_to_jpg_applies_exif_orientation() -> None:
    jpeg_bytes = _build_oriented_jpeg_bytes()

    converted_bytes = to_jpg(jpeg_bytes)

    with Image.open(BytesIO(converted_bytes)) as image:
        image.load()
        assert image.format == 'JPEG'
        assert image.size == (20, 40)
        top_pixel = image.getpixel((10, 10))
        bottom_pixel = image.getpixel((10, 30))
        assert top_pixel[0] > top_pixel[1]
        assert bottom_pixel[1] > bottom_pixel[0]


def _build_png_bytes(*, mode: str) -> bytes:
    color = (10, 20, 30) if mode == 'RGB' else (10, 20, 30, 0)
    image = Image.new(mode, (4, 4), color)
    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


def _build_oriented_jpeg_bytes() -> bytes:
    image = Image.new('RGB', (40, 20))
    for x in range(20):
        for y in range(20):
            image.putpixel((x, y), (255, 0, 0))
    for x in range(20, 40):
        for y in range(20):
            image.putpixel((x, y), (0, 255, 0))

    exif = image.getexif()
    exif[274] = 6

    output = BytesIO()
    image.save(output, format='JPEG', exif=exif)
    return output.getvalue()
