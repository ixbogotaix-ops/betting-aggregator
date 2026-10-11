from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Замените строку подключения на ваши реальные данные
# Переключено на SQLite для того, чтобы всё работало сразу "из коробки" без настройки серверов
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./betting_db.sqlite"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
