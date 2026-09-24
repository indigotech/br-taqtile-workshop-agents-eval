from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.models import Budget, Preference, User
from app.data.user_data_source import UserDataSource


class GetUserProfileInput(BaseModel):
    user_id: int = Field(description="Id do usuário no banco")


class GetUserProfileOutput(BaseModel):
    found: bool
    user: User | None
    budget: Budget | None
    preferences: list[Preference]


class GetUserProfileTool(Tool[GetUserProfileInput, GetUserProfileOutput]):
    name = "get_user_profile"
    description = (
        "Busca o perfil do usuário: dados cadastrais, orçamento por categoria "
        "e preferências (comida, atividades, hospedagem e restrições)."
    )
    input_model = GetUserProfileInput
    output_model = GetUserProfileOutput

    def __init__(self, user_data_source: UserDataSource) -> None:
        self.user_data_source = user_data_source

    def run(self, arguments: GetUserProfileInput) -> GetUserProfileOutput:
        user = self.user_data_source.get_user(arguments.user_id)
        if user is None:
            return GetUserProfileOutput(
                found=False, user=None, budget=None, preferences=[]
            )
        return GetUserProfileOutput(
            found=True,
            user=user,
            budget=self.user_data_source.get_budget(user.id),
            preferences=self.user_data_source.list_preferences(user.id),
        )
