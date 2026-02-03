from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from bot.config import config

engine = create_async_engine(config.db.url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database connection."""
    pass


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session
