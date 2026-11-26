"""Gunicorn settings (used automatically: `gunicorn wsgi:app`)."""
import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 4)))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"
timeout = 30
graceful_timeout = 20
keepalive = 5
max_requests = 1000          # recycle workers to avoid slow leaks
max_requests_jitter = 100
forwarded_allow_ips = "*"    # trust proxy headers (ProxyFix handles them in-app)
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
