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
    if not image_bytes:
        raise ValueError('image_bytes must not be empty')

    if isinstance(quality, bool) or not isinstance(quality, int):
        raise ValueError('quality must be an integer')
    if quality < 1 or quality > 100:
        raise ValueError('quality must be in 1..100')

    with Image.open(BytesIO(image_bytes)) as image:
        image.load()
        image = ImageOps.exif_transpose(image)

        if image.mode in {'RGBA', 'LA'} or (image.mode == 'P' and 'transparency' in image.info):
            rgba_image = image.convert('RGBA')
            flattened_image = Image.new('RGB', rgba_image.size, 'white')
            flattened_image.paste(rgba_image, mask=rgba_image.getchannel('A'))
            output_image = flattened_image
        elif image.mode != 'RGB':
            output_image = image.convert('RGB')
        else:
            output_image = image

        output = BytesIO()
        output_image.save(
            output,
            format='JPEG',
            quality=quality,
            subsampling=0,
            optimize=True,
            progressive=True,
        )
        return output.getvalue()
