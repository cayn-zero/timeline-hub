from io import BytesIO

from PIL import Image, ImageOps


def to_jpg(image_bytes: bytes, *, quality: int = 95) -> bytes:
    """Convert image bytes to JPEG bytes.

    Args:
        image_bytes: Source image bytes in a Pillow-readable format.
        quality: JPEG quality in the closed range 1..100.

    Raises:
        ValueError: If parameters are invalid.
    """
    _validate_image_bytes(image_bytes)
    _validate_quality(quality)

    with Image.open(BytesIO(image_bytes)) as image:
        image.load()
        image = ImageOps.exif_transpose(image)
        output_image = _normalize_to_rgb(image)

        return _save_jpg(output_image, quality=quality)


def normalize_cover_to_jpg(
    image_bytes: bytes,
    *,
    max_height: int = 1280,
    quality: int = 95,
) -> bytes:
    """Normalize cover image bytes to the stored JPEG invariant.

    Already-valid JPEG inputs may be returned unchanged when no resize,
    EXIF normalization, or RGB normalization is needed. In that case,
    `quality` is not applied because no re-encoding occurs.

    Args:
        image_bytes: Source image bytes in a Pillow-readable format.
        max_height: Maximum allowed output height in pixels.
        quality: JPEG quality in the closed range 1..100.

    Raises:
        ValueError: If parameters are invalid.
    """
    _validate_image_bytes(image_bytes)
    _validate_quality(quality)
    _validate_max_height(max_height)

    is_jpeg = image_bytes.startswith(b'\xff\xd8\xff')

    with Image.open(BytesIO(image_bytes)) as image:
        image.load()
        needs_exif_transpose = _needs_exif_transpose(image)
        image = ImageOps.exif_transpose(image)

        width, height = image.size
        needs_resize = height > max_height
        needs_rgb_normalization = _needs_rgb_normalization(image)

        if is_jpeg and not needs_exif_transpose and not needs_resize and not needs_rgb_normalization:
            return image_bytes

        output_image = _normalize_to_rgb(image)
        if needs_resize:
            new_width = max(1, round(width * max_height / height))
            output_image = output_image.resize((new_width, max_height), Image.Resampling.LANCZOS)

        return _save_jpg(output_image, quality=quality)


def _validate_image_bytes(image_bytes: bytes) -> None:
    if not image_bytes:
        raise ValueError('image_bytes must not be empty')


def _validate_quality(quality: int) -> None:
    if isinstance(quality, bool) or not isinstance(quality, int):
        raise ValueError('quality must be an integer')
    if quality < 1 or quality > 100:
        raise ValueError('quality must be in 1..100')


def _validate_max_height(max_height: int) -> None:
    if isinstance(max_height, bool) or not isinstance(max_height, int):
        raise ValueError('max_height must be an integer')
    if max_height < 1:
        raise ValueError('max_height must be >= 1')


def _needs_exif_transpose(image: Image.Image) -> bool:
    return image.getexif().get(274, 1) != 1


def _needs_rgb_normalization(image: Image.Image) -> bool:
    # Any non-RGB mode requires normalization to RGB before JPEG encoding.
    return image.mode != 'RGB'


def _normalize_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in {'RGBA', 'LA'} or (image.mode == 'P' and 'transparency' in image.info):
        rgba_image = image.convert('RGBA')
        flattened_image = Image.new('RGB', rgba_image.size, 'white')
        flattened_image.paste(rgba_image, mask=rgba_image.getchannel('A'))
        return flattened_image
    if image.mode != 'RGB':
        return image.convert('RGB')
    return image


def _save_jpg(image: Image.Image, *, quality: int) -> bytes:
    output = BytesIO()
    image.save(
        output,
        format='JPEG',
        quality=quality,
        subsampling=0,
        optimize=True,
        progressive=True,
    )
    return output.getvalue()
