from typing import List

from ...application.query.order.get_order_pagination_query import GetOrderPaginationQuery, GetOrderPaginationQueryHandler
from ...application.query.order.get_order_by_id_query import GetOrderByIdQuery, GetOrderByIdQueryHandler
from ...application.command.order.handle_payment_return_command import HandlePaymentReturnCommand, HandlePaymentReturnCommandHandler
from ...application.query.order.get_order_payment_url_query import GetOrderPaymentUrlQuery, GetOrderPaymentUrlQueryHandler
from ...application.command.order.update_order_status_command import UpdateOrderStatusCommand, UpdateOrderStatusCommandHandler
from ...application.command.order.take_responsibility_for_order_command import TakeResponsibilityForOrderCommand, TakeResponsibilityForOrderCommandHandler
from ...domain.repository.meal_repository import MealRepository
from ...application.schema.response.order_response_schema import CreateOrderResponse, GetOrderByIdResponse, GetOrderPaginationResponse, GetOrderPaymentUrlResponse, HandlePaymentReturnResponse, TakeResponsibilityForOrderResponse, UpdateOrderStatusResponse
from ...domain.repository.order_repository import OrderRepository
from ...application.command.order.create_order_command import CreateOrderCommand, CreateOrderCommandHandler


class OrderService:
    order_repository: OrderRepository
    meal_repository: MealRepository

    def __init__(self, order_repository: OrderRepository, meal_repository: MealRepository):
        self.order_repository = order_repository
        self.meal_repository = meal_repository

    async def create_order(self, meals_ids: List[int]) -> CreateOrderResponse:
        command = CreateOrderCommand(meal_ids=meals_ids)
        command_handler = CreateOrderCommandHandler(
            meal_repository=self.meal_repository,
            order_repository=self.order_repository
        )
        return await command_handler.handle(command=command)

    async def take_responsibility_for_order(self, order_id: int, staff_id: int) -> TakeResponsibilityForOrderResponse:
        command = TakeResponsibilityForOrderCommand(order_id=order_id, staff_id=staff_id)
        command_handler = TakeResponsibilityForOrderCommandHandler(
            order_repository=self.order_repository
        )
        return await command_handler.handle(command=command)

    async def update_order_status(self, staff_id: int, order_id: int, status: str) -> UpdateOrderStatusResponse:
        command = UpdateOrderStatusCommand(order_id=order_id, staff_id=staff_id, status=status)
        command_handler = UpdateOrderStatusCommandHandler(
            order_repository=self.order_repository,
            meal_repository=self.meal_repository,
        )
        return await command_handler.handle(command=command)

    async def get_order_payment_url(self, order_id: int, client_ip_address: str) -> GetOrderPaymentUrlResponse:
        query = GetOrderPaymentUrlQuery(order_id=order_id, client_ip_address=client_ip_address)
        query_handler = GetOrderPaymentUrlQueryHandler(
            order_repository=self.order_repository
        )
        return await query_handler.handle(query=query)

    async def handle_payment_return(self, query_params: dict) -> HandlePaymentReturnResponse:
        command = HandlePaymentReturnCommand(query_params=query_params)
        command_handler = HandlePaymentReturnCommandHandler(order_repository=self.order_repository)
        return await command_handler.handle(command=command)

    async def get_order_by_id(self, order_id: int) -> GetOrderByIdResponse:
        query = GetOrderByIdQuery(order_id=order_id)
        query_handler = GetOrderByIdQueryHandler(
            meal_repository=self.meal_repository,
            order_repository=self.order_repository,
        )
        return await query_handler.handle(query=query)

    async def get_order_pagination(self, page: int, size: int, is_order_responsible: bool | None) -> GetOrderPaginationResponse:
        query = GetOrderPaginationQuery(page=page, size=size, is_order_responsible=is_order_responsible)
        query_handler = GetOrderPaginationQueryHandler(
            order_repository=self.order_repository,
            meal_repository=self.meal_repository,
        )
        return await query_handler.handle(query=query)
