from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from sqlalchemy.pool import NullPool

from user.models import Base

DATABASE_URL = "postgresql+asyncpg://postgres:said2000@localhost:5432/fastapi"

# DATABASE_URL = 'sqlite+aiosqlite:///base.db'

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


# async def get_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
# async def delete_table():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)