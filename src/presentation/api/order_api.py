from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi_limiter.depends import RateLimiter
from starlette import status
from fastapi_cache.decorator import cache
from fastapi_cache import JsonCoder

from ...application.socket_manager.staff_manager import staff_manager
from ...infrastructure.config.rate_limiting import identifier_based_on_claims
from ...infrastructure.config.caching import REDIS_PREFIX, FastAPICacheExtended, RedisNamespace
from ...infrastructure.utils.validator import validate_is_order_responsible, validate_page, validate_size
from ...application.socket_manager.order_manager import order_manager
from ...infrastructure.config.security import verify_access_token
from ...infrastructure.utils.token_util import TokenClaims
from ...application.service.order_service import OrderService
from ...infrastructure.config.dependencies import get_order_service
from ...application.schema.request.order_request_schema import CreateOrderRequest, UpdateOrderStatusRequest
from ...application.schema.response.order_response_schema import (
    CreateOrderResponse,
    GetOrderByIdResponse,
    GetOrderPaginationResponse,
    GetOrderPaymentUrlResponse,
    HandlePaymentReturnResponse,
    TakeResponsibilityForOrderResponse,
    UpdateOrderStatusResponse
)

router = APIRouter(prefix="/order", tags=["Order"])

@router.post(
    path="/create",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateOrderResponse,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def create_order(
    request: CreateOrderRequest,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    background_tasks: BackgroundTasks,
):
    response = await order_service.create_order(meals_ids=request.meals)
    background_tasks.add_task(staff_manager.broadcast_new_order, order_id=response.id)
    return response

@router.put(
    path="/take-responsibility",
    status_code=status.HTTP_200_OK,
    response_model=TakeResponsibilityForOrderResponse,
    dependencies=[
        Depends(verify_access_token),
        Depends(RateLimiter(times=10, seconds=60, identifier=identifier_based_on_claims))
    ]
)
async def take_responsibility_for_order(
    claims: Annotated[TokenClaims, Depends(verify_access_token)],
    order_id: int,
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    return await order_service.take_responsibility_for_order(order_id=order_id, staff_id=claims.id)

@router.put(
    path="/update-status",
    status_code=status.HTTP_200_OK,
    response_model=UpdateOrderStatusResponse,
    dependencies=[
        Depends(verify_access_token),
        Depends(RateLimiter(times=20, seconds=60, identifier=identifier_based_on_claims))
    ]
)
async def update_order_status(
    claims: Annotated[TokenClaims, Depends(verify_access_token)],
    request: UpdateOrderStatusRequest,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    background_tasks: BackgroundTasks
):
    response = await order_service.update_order_status(order_id=request.order_id, staff_id=claims.id, status=request.status)
    background_tasks.add_task(order_manager.broadcast, response.id, response.order_status)
    return response

@router.get(
    path="/payment-url/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetOrderPaymentUrlResponse,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
@cache(
    expire=60 * 10,
    namespace=RedisNamespace.PAYMENT_URL,
    coder=JsonCoder,
    key_builder=lambda func, namespace="", *, request=None, response=None, args=(), kwargs={}: (
        ":".join([
            namespace,
            str(kwargs.get("order_id"))
        ])
    )
)
async def get_order_payment_url(
    order_id: int,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    request: Request
):
    return await order_service.get_order_payment_url(
        order_id=order_id,
        client_ip_address=request.client.host if request.client else "Unknown"
    )

@router.get(path="/payment-return", status_code=status.HTTP_200_OK, response_model=HandlePaymentReturnResponse)
async def handle_payment_return(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    request: Request,
    background_tasks: BackgroundTasks,
):
    response = await order_service.handle_payment_return(query_params=dict(request.query_params))
    background_tasks.add_task(
        FastAPICacheExtended.clear,
        key=":".join([REDIS_PREFIX, RedisNamespace.PAYMENT_URL, str(response.order_id)])
    )
    return response

@router.get(
    path="/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetOrderByIdResponse,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
async def get_order_by_id(order_id: int, order_service: Annotated[OrderService, Depends(get_order_service)]):
    return await order_service.get_order_by_id(order_id=order_id)

@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    response_model=GetOrderPaginationResponse,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
async def get_order_pagination(
    page: Annotated[int, Depends(validate_page)],
    size: Annotated[int, Depends(validate_size)],
    is_order_responsible: Annotated[bool, Depends(validate_is_order_responsible)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    return await order_service.get_order_pagination(page=page, size=size, is_order_responsible=is_order_responsible)
