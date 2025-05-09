from concurrent.futures import ProcessPoolExecutor
from typing import Optional, List
from fastapi import UploadFile
from redis.asyncio import Redis

from ...application.command.meal.update_meal_image_command import UpdateMealImageCommand, UpdateMealImageCommandHandler
from ...application.command.meal.update_meal_data_command import UpdateMealDataCommand, UpdateMealDataCommandHandler
from ...application.query.meal.get_meals_query import GetMealsQuery, GetMealsQueryHandler
from ...application.query.meal.get_meal_by_id_query import GetMealByIdQuery, GetMealByIdQueryHandler
from ...application.command.meal.enable_meal_command import EnableMealCommand, EnableMealCommandHandler
from ...application.command.meal.disable_meal_command import DisableMealCommand, DisableMealCommandHandler
from ...application.command.meal.create_meal_command import CreateMealCommand, CreateMealCommandHandler
from ...application.schema.response.meal_response_schema import CreateMealResponse, DisableMealResponse, EnableMealResponse, GetMealResponse, GetMealsResponse, UpdateMealDataResponse, UpdateMealImageResponse
from ...domain.repository.meal_repository import MealRepository


class MealService:
    meal_repository: MealRepository
    process_executor: ProcessPoolExecutor
    redlock_connection_manager: List[Redis]

    def __init__(
        self,
        meal_repository: MealRepository,
        process_executor: ProcessPoolExecutor,
        redlock_connection_manager: List[Redis],
    ):
        self.meal_repository = meal_repository
        self.process_executor = process_executor
        self.redlock_connection_manager = redlock_connection_manager

    async def enable_meal(self, id: int) -> EnableMealResponse:
        command = EnableMealCommand(id=id)
        command_handler = EnableMealCommandHandler(meal_repository=self.meal_repository)
        return await command_handler.handle(command=command)

    async def disable_meal(self, id: int) -> DisableMealResponse:
        command = DisableMealCommand(id=id)
        command_handler = DisableMealCommandHandler(meal_repository=self.meal_repository)
        return await command_handler.handle(command=command)

    async def create_meal(self, name: str, description: str, price: int, picture: UploadFile) -> CreateMealResponse:
        command = CreateMealCommand(name=name, description=description, price=price, picture=picture)
        command_handler = CreateMealCommandHandler(
            meal_repository=self.meal_repository,
            executor=self.process_executor,
        )
        return await command_handler.handle(command=command)

    async def get_meal_by_id(self, id: int) -> GetMealResponse:
        query = GetMealByIdQuery(id=id)
        query_handler = GetMealByIdQueryHandler(meal_repository=self.meal_repository)
        return await query_handler.handle(query=query)

    async def get_meals(self, page: int, size: int, is_available: bool | None) -> GetMealsResponse:
        query = GetMealsQuery(page=page, size=size, is_available=is_available)
        query_handler = GetMealsQueryHandler(meal_repository=self.meal_repository)
        return await query_handler.handle(query=query)

    async def update_meal_data(self, id: int, name: Optional[str], description: Optional[str], price: Optional[int]) -> UpdateMealDataResponse:
        command = UpdateMealDataCommand(
            id=id,
            name=name,
            description=description,
            price=price
        )
        command_handler = UpdateMealDataCommandHandler(meal_repository=self.meal_repository)
        return await command_handler.handle(command=command)

    async def update_meal_image(self, id: int, picture: UploadFile) -> UpdateMealImageResponse:
        command = UpdateMealImageCommand(
            id=id,
            picture=picture,
        )
        command_handler = UpdateMealImageCommandHandler(
            meal_repository=self.meal_repository,
            executor=self.process_executor,
            redlock_connection_manager=self.redlock_connection_manager
        )
        return await command_handler.handle(command=command)
