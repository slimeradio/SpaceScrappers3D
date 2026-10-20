"""Small lossless RGBA PNG writer for Blender's bundled numpy; no pip installs."""
import struct
import zlib
from pathlib import Path


def write_png(path, pixels, bits=8, srgb=False):
    import numpy as np
    if not np.isfinite(pixels).all():
        raise ValueError('Non-finite image data: ' + str(path))
    h, w, channels = pixels.shape
    if channels != 4 or bits not in (8, 16):
        raise ValueError('Expected RGBA8 or RGBA16')
    dtype = np.uint8 if bits == 8 else np.dtype('>u2')
    quantized = np.rint(np.clip(pixels, 0, 1) * ((1 << bits) - 1)).astype(dtype)
    rows = b''.join(b'\0' + quantized[y].tobytes() for y in range(h))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, bits, 6, 0, 0, 0))
    data += chunk(b'sRGB', b'\0') if srgb else chunk(b'gAMA', struct.pack('>I', 100000))
    data += chunk(b'IDAT', zlib.compress(rows, 6)) + chunk(b'IEND', b'')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
