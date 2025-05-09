from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from fastapi import Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from concurrent.futures import ProcessPoolExecutor

from .presentation.websocket import staff_websocket
from .infrastructure.config.redlock_connection_manager import redlock_connection_manager
from .infrastructure.config.rate_limiting import (
    RATE_LIMITTING_CACHE_PREFIX,
    http_callback_exception_handler
)
from .presentation.websocket import order_websocket
from .presentation.api import order_api
from .infrastructure.config.variables import UPLOAD_FOLDER
from .presentation.api import meal_api
from .presentation.api import manager_api
from .presentation.api import user_api
from .infrastructure.config.database import init_db
from .infrastructure.config.exception_handler import (
    process_http_exception,
    process_validation_error,
    process_global_exception,
    process_web_socket_exception
)
from .infrastructure.config.caching import REDIS_PREFIX, redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    FastAPICache.init(RedisBackend(redis), prefix=REDIS_PREFIX)
    await FastAPILimiter.init(
        redis=redis,
        prefix=RATE_LIMITTING_CACHE_PREFIX,
        http_callback=http_callback_exception_handler
    )
    app.state.process_executor = ProcessPoolExecutor()
    app.state.redlock_connection_manager = redlock_connection_manager
    yield
    await redis.close()
    await FastAPILimiter.close()
    app.state.process_executor.shutdown(wait=True)
    for redlock_connection in app.state.redlock_connection_manager:
        await redlock_connection.close()


app = FastAPI(title="Anteiku Kohi", lifespan=lifespan)

origins = [
    "*"
]

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

app.mount("/public/images", StaticFiles(directory=UPLOAD_FOLDER), name="images")

app.include_router(user_api.router)
app.include_router(manager_api.router)
app.include_router(meal_api.router)
app.include_router(order_api.router)

app.include_router(order_websocket.router)
app.include_router(staff_websocket.router)

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return process_http_exception(exc)

@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    return process_validation_error(exc)

@app.exception_handler(RequestValidationError)
def request_validation_error_handler(request: Request, exc: RequestValidationError):
    return process_validation_error(exc)

@app.exception_handler(WebSocketException)
async def web_socket_exception_handler(websocket: WebSocket, exc: WebSocketException):
    await process_web_socket_exception(websocket, exc)

@app.exception_handler(Exception)
def exception_handler(request: Request, exc: Exception):
    return process_global_exception(exc)
