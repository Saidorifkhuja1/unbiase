from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

class Base(DeclarativeBase):
    pass

DATABASE_URL = "postgresql+asyncpg://postgres:start2024@localhost:5434/unibase"

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
    try:
        async with async_session() as session:
            yield session
    except Exception as e:
        print("Database connection error:", e)



# async def get_db() -> AsyncSession:
#     async with async_session() as session:
#
#         yield session


async def init_db():
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)


