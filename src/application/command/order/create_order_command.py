from collections import Counter
from typing import Dict, List

from ....infrastructure.utils.create_payment_url import create_payment_url

from ....infrastructure.config.variables import VNPAY_RETURN_URL, VNPAY_TMN_CODE

from ....application.schema.response.order_response_schema import CreateOrderResponse, OrderMealResponse
from ....domain.entity.meal_entity import MealEntity
from ....domain.entity.order_meal_entity import OrderMealEntity
from ....domain.repository.order_repository import OrderRepository
from ....domain.repository.meal_repository import MealRepository
from datetime import datetime

class CreateOrderCommand:
    meal_ids: List[int]
    client_ip_address: str

    def __init__(self, meal_ids: List[int], client_ip_address: str):
        self.meal_ids = meal_ids
        self.client_ip_address = client_ip_address

class CreateOrderCommandHandler:
    order_repository: OrderRepository
    meal_repository: MealRepository

    def __init__(self, order_repository: OrderRepository, meal_repository: MealRepository):
        self.order_repository = order_repository
        self.meal_repository = meal_repository

    async def handle(self, command: CreateOrderCommand) -> CreateOrderResponse:
        meal_counts = Counter(command.meal_ids)
        meals_with_quantities: Dict[MealEntity, int] = {}
        meal_lookup: Dict[int, MealEntity] = {}
        for meal_id in set(command.meal_ids):
            meal = await self.meal_repository.get_by_id(meal_id)
            if meal and meal.is_available:
                meals_with_quantities[meal] = meal_counts[meal_id]
                meal_lookup[meal.id] = meal
        new_order = await self.order_repository.create_order(
            meals=[
                OrderMealEntity(
                    id=-1,
                    order_id=-1,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    meal_id=meal.id,
                    quantity=quantity,
                    price=meal.price,
                )
                for meal, quantity in meals_with_quantities.items()
            ]
        )
        payment_url_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': VNPAY_TMN_CODE,
            'vnp_Amount': sum(meal.price * quantity for meal, quantity in meals_with_quantities.items()) * 100,
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': f'{new_order.id}',
            'vnp_OrderInfo': f'Anteiku Kohi - Mã hóa đơn {new_order.id}',
            'vnp_OrderType': 'Thanh toán hóa đơn',
            'vnp_Locale': 'vn',
            'vnp_CreateDate': new_order.created_at.strftime('%Y%m%d%H%M%S'),
            'vnp_IpAddr': command.client_ip_address,
            'vnp_ReturnUrl': VNPAY_RETURN_URL
        }
        payment_url = create_payment_url(payment_url_params)
        await self.order_repository.update_order_payment_url(order_id=new_order.id, payment_url=payment_url)
        order_meal_list = await self.order_repository.get_order_meal_list(order_id=new_order.id)
        return CreateOrderResponse(
            id=new_order.id,
            updated_at=new_order.updated_at,
            created_at=new_order.created_at,
            order_status=new_order.order_status,
            payment_status=new_order.payment_status,
            meals=[
                OrderMealResponse(
                    id=order_meal.id,
                    price=order_meal.price,
                    quantity=order_meal.quantity,
                    name=meal_lookup[order_meal.meal_id].name,
                    description=meal_lookup[order_meal.meal_id].description,
                    image_url=meal_lookup[order_meal.meal_id].image_url,
                )
                for order_meal in order_meal_list
            ]
        )
