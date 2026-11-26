"""Image uploads (recipe visual reference, ingredient request photo), stored in PostgreSQL."""
import secrets

from flask_login import current_user
from sqlalchemy import text

from .extensions import db
from .models import Image

MAX_BYTES = 3 * 1024 * 1024
PREFIX = "/img/"
# Detect type from file content, not the client-supplied name/mimetype
SIGNATURES = [(b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG\r\n\x1a\n", "image/png")]


class UploadError(ValueError):
    pass


def _sniff(head):
    for sig, mime in SIGNATURES:
        if head.startswith(sig):
            return mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def save_image(storage):
    """Validate an uploaded image and add it to the current DB session.
    Returns its public URL (/img/<id>), or None when no file was sent.
    The caller's commit saves it; a rollback discards it."""
    if not storage or not storage.filename:
        return None
    data = storage.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise UploadError("Ukuran gambar maksimal 3 MB.")
    mime = _sniff(data[:16])
    if not mime:
        raise UploadError("Format gambar harus JPG, PNG, atau WEBP.")
    image = Image(id=secrets.token_hex(16), mime=mime, data=data, size=len(data),
                  uploaded_by=current_user.id if current_user.is_authenticated else None)
    db.session.add(image)
    return PREFIX + image.id


def remove_upload(url):
    """Delete a stored image by its URL (no-op for other URLs)."""
    if url and url.startswith(PREFIX):
        db.session.execute(text("DELETE FROM images WHERE id = :id"), {"id": url[len(PREFIX):]})
        db.session.commit()
