import asyncio
import tempfile
from datetime import timedelta
from pathlib import Path


async def _download_audio_as_opus_internal(
    url: str,
    *,
    download_cover: bool,
    timeout: timedelta,
) -> tuple[bytes, bytes | None]:
    if not isinstance(url, str):
        raise ValueError('url must be a string')

    normalized_url = url.strip()
    if not normalized_url:
        raise ValueError('url must not be empty')

    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = Path(temp_dir) / 'audio.%(ext)s'
        args: list[str] = [
            'yt-dlp',
            '-f',
            'bestaudio[acodec=opus]/bestaudio',
            '--extract-audio',
            '--audio-format',
            'opus',
            '--quiet',
            '--no-playlist',
        ]
        if download_cover:
            args.extend(
                [
                    '--write-thumbnail',
                    '--convert-thumbnails',
                    'jpg',
                ]
            )
        args.extend(['-o', str(output_template), normalized_url])
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout.total_seconds(),
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise

        if proc.returncode != 0:
            stderr_text = stderr.decode(errors='replace')
            raise RuntimeError(f'yt-dlp failed: {stderr_text}')

        output_files = sorted(Path(temp_dir).glob('*.opus'))
        if not output_files:
            raise RuntimeError('yt-dlp did not produce opus output')
        if len(output_files) > 1:
            raise RuntimeError('yt-dlp produced multiple opus outputs')

        audio_bytes = output_files[0].read_bytes()
        if not audio_bytes.startswith(b'OggS'):
            raise RuntimeError('yt-dlp output is not a valid Ogg/Opus container')

        if not download_cover:
            return audio_bytes, None

        cover_files = sorted(Path(temp_dir).glob('*.jpg'))
        if not cover_files:
            return audio_bytes, None
        if len(cover_files) > 1:
            raise RuntimeError('yt-dlp produced multiple cover outputs')

        cover_bytes = cover_files[0].read_bytes()
        if not cover_bytes:
            raise RuntimeError('yt-dlp produced empty cover output')
        return audio_bytes, cover_bytes


async def download_audio_as_opus(
    url: str,
    *,
    timeout: timedelta = timedelta(minutes=3),
) -> bytes:
    """Download one URL audio track as Opus bytes using `yt-dlp`.

    Args:
        url: Source URL to download.
        timeout: Maximum time allowed for the `yt-dlp` subprocess run.

    Raises:
        ValueError: If `url` is invalid.
        RuntimeError: If `yt-dlp` fails or output validation fails.
    """
    audio, _ = await _download_audio_as_opus_internal(
        url,
        download_cover=False,
        timeout=timeout,
    )
    return audio


async def download_audio_as_opus_and_cover(
    url: str,
    *,
    timeout: timedelta = timedelta(minutes=3),
) -> tuple[bytes, bytes]:
    """Download one URL audio track as Opus bytes and cover as JPG bytes using `yt-dlp`.

    Args:
        url: Source URL to download.
        timeout: Maximum time allowed for the `yt-dlp` subprocess run.

    Raises:
        ValueError: If `url` is invalid.
        RuntimeError: If `yt-dlp` fails or output validation fails.
    """
    audio, cover = await _download_audio_as_opus_internal(
        url,
        download_cover=True,
        timeout=timeout,
    )
    if cover is None:
        raise RuntimeError('yt-dlp did not produce cover output')
    return audio, cover
