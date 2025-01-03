from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from sqlalchemy.pool import NullPool

from user.models import Base

DATABASE_URL = "postgresql+asyncpg://postgres:said2000@localhost:5432/fastapi"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=NullPool
)


async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)





async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)
