"""
Gunicorn config for production. Uses uvicorn's ASGI worker class so
FastAPI's async endpoints (and the startup event that loads the model)
work correctly under gunicorn's process manager.

Worker count follows the standard (2 * CPU cores) + 1 formula, capped at 4
since this service is CPU-bound on model inference, not I/O-bound -- more
workers just means more copies of the model in memory, not more
throughput past a point.
"""
import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = min((multiprocessing.cpu_count() * 2) + 1, 4)

timeout = 30
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

# Each worker loads its own copy of the model at startup (via FastAPI's
# @app.on_event("startup")) -- no shared state needed since inference is
# stateless per-request.
preload_app = False
