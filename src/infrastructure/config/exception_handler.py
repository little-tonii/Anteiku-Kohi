from fastapi import HTTPException, WebSocket, WebSocketException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette import status

from ...application.schema.response.error_response_schema import ErrorResponse, ErrorsResponse

def process_http_exception(exc: HTTPException):
    message = exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=message).model_dump()
    )

def process_validation_error(exc: ValidationError | RequestValidationError):
    messages = []
    for error in exc.errors():
        error_type = error["type"]
        error_msg = error["msg"]
        if error_type == "json_invalid":
            messages.append("JSON không hợp lệ")
        elif error_type == "missing":
            messages.append("Thiếu trường thông tin")
        elif error_type == "value_error":
            messages.append(error_msg.split(", ")[-1])
        else:
            messages.append(f"{error_type} {error_msg}")
    if len(messages) == 1:
        return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=messages[0]).model_dump()
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorsResponse(messages=messages).model_dump()
    )

async def process_web_socket_exception(websocket: WebSocket, exc: WebSocketException):
    await websocket.close(code=exc.code, reason=exc.reason)

def process_global_exception(exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(message="Có lỗi xảy ra").model_dump()
    )
