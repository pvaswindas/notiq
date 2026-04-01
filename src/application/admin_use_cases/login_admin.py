from dataclasses import dataclass

from src.application.services.auth_service import AdminAuthService, AdminLoginResult


@dataclass(slots=True, frozen=True)
class LoginAdminInput:
    email: str
    password: str


class LoginAdminUseCase:
    def __init__(self, auth_service: AdminAuthService) -> None:
        self._auth_service = auth_service

    async def execute(self, dto: LoginAdminInput) -> AdminLoginResult:
        return await self._auth_service.login(email=dto.email, password=dto.password)
