"""Serve uploaded images from PostgreSQL with long-lived caching (ids are random and never reused)"""
from flask import Blueprint, Response, abort, request

from ..extensions import db, limiter
from ..models import Image

bp = Blueprint("media", __name__)


@bp.get("/img/<string:image_id>")
@limiter.exempt
def image(image_id):
    if len(image_id) != 32 or not all(c in "0123456789abcdef" for c in image_id):
        abort(404)
    etag = f'"{image_id}"'
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304)
    img = db.session.get(Image, image_id)
    if not img:
        abort(404)
    resp = Response(img.data, mimetype=img.mime)
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"  # Vercel's CDN caches it too
    resp.headers["ETag"] = etag
    return resp
