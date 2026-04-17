from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserOut


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def signup(self, payload: SignupRequest, settings) -> AuthResponse:
        existing = await self.session.scalar(select(User).where(User.email == payload.email))
        if existing:
            raise AppError("Email already registered", status_code=409, code="email_exists")

        user = User(
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        token = create_access_token(user.id, settings)
        return AuthResponse(user=self._user_to_out(user), access_token=token)

    async def login(self, payload: LoginRequest, settings) -> AuthResponse:
        user = await self.session.scalar(select(User).where(User.email == payload.email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppError("Invalid email or password", status_code=401, code="invalid_credentials")

        token = create_access_token(user.id, settings)
        return AuthResponse(user=self._user_to_out(user), access_token=token)

    @staticmethod
    def _user_to_out(user: User) -> UserOut:
        return UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
        )
