from io import BytesIO

import pytest
from PIL import Image

from timeline_hub.infra.images import normalize_cover_to_jpg, to_jpg


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


def test_normalize_cover_to_jpg_returns_original_bytes_for_small_jpeg() -> None:
    jpeg_bytes = _build_jpeg_bytes(size=(640, 640))

    normalized_bytes = normalize_cover_to_jpg(jpeg_bytes)

    assert normalized_bytes == jpeg_bytes


def test_normalize_cover_to_jpg_resizes_large_jpeg_without_upscaling_width_ratio() -> None:
    jpeg_bytes = _build_jpeg_bytes(size=(1500, 2000))

    normalized_bytes = normalize_cover_to_jpg(jpeg_bytes)

    assert normalized_bytes != jpeg_bytes
    assert normalized_bytes.startswith(b'\xff\xd8\xff')
    with Image.open(BytesIO(normalized_bytes)) as image:
        image.load()
        assert image.format == 'JPEG'
        assert image.size == (960, 1280)


def test_normalize_cover_to_jpg_converts_small_png_without_upscaling() -> None:
    png_bytes = _build_png_bytes(mode='RGB', size=(600, 800))

    normalized_bytes = normalize_cover_to_jpg(png_bytes)

    assert normalized_bytes.startswith(b'\xff\xd8\xff')
    with Image.open(BytesIO(normalized_bytes)) as image:
        image.load()
        assert image.format == 'JPEG'
        assert image.size == (600, 800)


def test_normalize_cover_to_jpg_converts_and_clips_tall_png() -> None:
    png_bytes = _build_png_bytes(mode='RGBA', size=(900, 1800))

    normalized_bytes = normalize_cover_to_jpg(png_bytes)

    assert normalized_bytes.startswith(b'\xff\xd8\xff')
    with Image.open(BytesIO(normalized_bytes)) as image:
        image.load()
        assert image.format == 'JPEG'
        assert image.mode == 'RGB'
        assert image.size == (640, 1280)


def _build_png_bytes(*, mode: str, size: tuple[int, int] = (4, 4)) -> bytes:
    color = (10, 20, 30) if mode == 'RGB' else (10, 20, 30, 0)
    image = Image.new(mode, size, color)
    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


def _build_jpeg_bytes(*, size: tuple[int, int]) -> bytes:
    image = Image.new('RGB', size, (10, 20, 30))
    output = BytesIO()
    image.save(
        output,
        format='JPEG',
        quality=95,
        subsampling=0,
        optimize=True,
        progressive=True,
    )
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
