from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """The single declarative base for all future SQLAlchemy models."""