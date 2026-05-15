from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.database_schema)


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from app.models.classification_job import ClassificationJob
    from app.models.classification_result import ClassificationResult
    from app.models.extracted_transaction import ExtractedTransaction
    from app.models.user_correction import UserCorrection

    with engine.begin() as connection:
        connection.execute(
            text(f'CREATE SCHEMA IF NOT EXISTS "{settings.database_schema}" AUTHORIZATION CURRENT_USER')
        )

    Base.metadata.create_all(
        bind=engine,
        tables=[
            ClassificationJob.__table__,
            ExtractedTransaction.__table__,
            ClassificationResult.__table__,
            UserCorrection.__table__,
        ],
    )
