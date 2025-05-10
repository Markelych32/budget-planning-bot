from typing import TypeVar

from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

from src.infrastructure.database.constants import IncomeSource

__all__ = (
    "Base",
    "ConcreteSchema",
    "UserSchema",
    "ConfigurationSchema",
    "CurrencySchema",
    "CurrencyExchangeSchema",
    "CategorySchema",
    "CostSchema",
    "IncomeSchema",
)

meta = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class _Base:

    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=_Base, metadata=meta)

ConcreteSchema = TypeVar("ConcreteSchema", bound=Base)


class UserSchema(Base):
    __tablename__ = "users"

    account_id = Column(Integer, nullable=False, unique=True)
    chat_id = Column(Integer, nullable=False)
    username = Column(String(length=100), nullable=False, unique=True)
    full_name = Column(String(length=100), nullable=False)

    configuration = relationship(
        "ConfigurationSchema", uselist=False, back_populates="user"
    )
    costs = relationship("CostSchema", back_populates="user")
    incomes = relationship("IncomeSchema", back_populates="user")


class ConfigurationSchema(Base):
    __tablename__ = "configurations"

    number_of_dates = Column(Integer, default=3, nullable=False)
    costs_sources = Column(Text)
    incomes_sources = Column(Text)
    ignore_categories = Column(Text)

    user_id = Column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    default_currency_id = Column(
        Integer, ForeignKey("currencies.id", ondelete="RESTRICT")
    )

    user = relationship("UserSchema", back_populates="configuration")
    default_currency = relationship(
        "CurrencySchema", uselist=False, back_populates="configurations"
    )


class CurrencySchema(Base):
    __tablename__ = "currencies"

    name = Column(String(length=3), nullable=False, unique=True)
    sign = Column(String(length=1), nullable=False, unique=True)
    equity = Column(Integer, nullable=False, default=0)

    configurations = relationship(
        "ConfigurationSchema", back_populates="default_currency"
    )
    costs = relationship("CostSchema", back_populates="currency")
    incomes = relationship("IncomeSchema", back_populates="currency")

    source_currency_exchanges = relationship(
        "CurrencyExchangeSchema",
        foreign_keys="[CurrencyExchangeSchema.source_currency_id]",
        back_populates="source_currency",
    )

    destination_currency_exchanges = relationship(
        "CurrencyExchangeSchema",
        foreign_keys="[CurrencyExchangeSchema.destination_currency_id]",
        back_populates="destination_currency",
    )


class CurrencyExchangeSchema(Base):
    __tablename__ = "currency_exchange"

    source_value = Column(Integer, nullable=False)
    destination_value = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    source_currency_id = Column(
        ForeignKey("currencies.id", ondelete="RESTRICT")
    )
    destination_currency_id = Column(
        ForeignKey("currencies.id", ondelete="RESTRICT")
    )
    user_id = Column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )

    source_currency = relationship(
        "CurrencySchema",
        foreign_keys=[source_currency_id],
        back_populates="source_currency_exchanges",
    )
    destination_currency = relationship(
        "CurrencySchema",
        foreign_keys=[destination_currency_id],
        back_populates="destination_currency_exchanges",
    )


class CategorySchema(Base):
    __tablename__ = "categories"

    name = Column(String, nullable=False)

    costs = relationship("CostSchema", uselist=True, back_populates="category")


class CostSchema(Base):
    __tablename__ = "costs"

    name = Column(String, nullable=False)
    value = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    user_id = Column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    category_id = Column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
    )
    currency_id = Column(
        ForeignKey("currencies.id", ondelete="RESTRICT"),
    )

    user = relationship("UserSchema", uselist=False, back_populates="costs")
    category = relationship(
        "CategorySchema", uselist=False, back_populates="costs"
    )
    currency = relationship(
        "CurrencySchema", uselist=False, back_populates="costs"
    )


class IncomeSchema(Base):
    __tablename__ = "incomes"

    name = Column(String, nullable=False)
    value = Column(Integer, nullable=False)
    source = Column(
        Enum(IncomeSource),
        nullable=False,
    )
    date = Column(Date, nullable=False)

    user_id = Column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    currency_id = Column(
        ForeignKey("currencies.id", ondelete="RESTRICT"),
    )

    user = relationship("UserSchema", uselist=False, back_populates="incomes")
    currency = relationship(
        "CurrencySchema", uselist=False, back_populates="incomes"
    )
