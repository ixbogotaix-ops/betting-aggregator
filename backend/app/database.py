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

async def init_db():
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for col_sql in [
            "ALTER TABLE predictions ADD COLUMN reasoning TEXT",
            "ALTER TABLE matches ADD COLUMN tactical_analysis TEXT",
            "ALTER TABLE matches ADD COLUMN key_factors TEXT"
        ]:
            try:
                await conn.execute(text(col_sql))
            except Exception:
                pass

        # Одноразовая миграция: сдвиг старых матчей UTC в Московское время (+3 часа)
        try:
            await conn.execute(text("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"))
            v_res = await conn.execute(text("SELECT version FROM schema_version WHERE version = 1"))
            if not v_res.scalar_one_or_none():
                await conn.execute(text("UPDATE matches SET match_date = datetime(match_date, '+3 hours')"))
                await conn.execute(text("INSERT INTO schema_version (version) VALUES (1)"))
        except Exception:
            pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

