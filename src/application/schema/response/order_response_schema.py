from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class OrderMealResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    image_url: str
    quantity: int

class CreateOrderResponse(BaseModel):
    id: int
    meals: List[OrderMealResponse]
    order_status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime

class TakeResponsibilityForOrderResponse(BaseModel):
    message: str

class UpdateOrderStatusResponse(BaseModel):
    id: int
    meals: List[OrderMealResponse]
    order_status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime
    staff_id: Optional[int]

class GetOrderPaymentUrlResponse(BaseModel):
    payment_url: str

class HandlePaymentReturnResponse(BaseModel):
    order_id: int
    message: str
    bank_code: str
    amount: int

class GetOrderByIdResponse(BaseModel):
    id: int
    meals: List[OrderMealResponse]
    order_status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime
    staff_id: Optional[int]

class GetOrderPaginationResponse(BaseModel):
    page: int
    size: int
    orders: List[GetOrderByIdResponse]
