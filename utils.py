import os
from PIL import Image as PILImage


def allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def make_thumbnail(original_path, thumbnail_path, scale=0.5):
    """Open an image, resize it to `scale` (e.g. 0.5 = 50%) of its
    original width/height, and save it to thumbnail_path.

    Returns (original_size, thumbnail_size) as (width, height) pairs."""
    with PILImage.open(original_path) as img:
        original_size = (img.width, img.height)
        new_width = max(1, int(img.width * scale))
        new_height = max(1, int(img.height * scale))
        thumbnail = img.resize((new_width, new_height))
        thumbnail.save(thumbnail_path)
    return original_size, (new_width, new_height)


def human_size(num_bytes):
    """Format a byte count as a short readable string, e.g. 48.2 KB."""
    if num_bytes is None:
        return "-"
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def save_avatar(file, save_path, size=200):
    """Open an uploaded avatar image, crop it to a centered square,
    resize to size x size, and save it to save_path."""
    with PILImage.open(file) as img:
        img = img.convert("RGB")
        side = min(img.width, img.height)
        left = (img.width - side) // 2
        top = (img.height - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize((size, size))
        img.save(save_path)
