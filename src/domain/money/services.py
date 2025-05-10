from decimal import Decimal, InvalidOperation

from src.infrastructure.errors import ValidationError


def validate(value: str | None = None) -> int:

    if not value:
        raise ValidationError("Value should exist")

    for char in (" ", "_", "-"):
        value = value.replace(char, "")

    value = value.replace(",", ".")

    if value.count(".") > 1:
        raise ValidationError("The value can not have more than one divider.")

    try:
        validated = Decimal(value) * 100
    except InvalidOperation:
        raise ValidationError("Value should be a valid number.")

    if validated < 0:
        raise ValidationError("Value should be greater than 0.")

    return int(validated)


def repr_value(value: int) -> str:

    solid_part = value // 100
    cents = value % 100

    return "{:,.2f}".format(float(solid_part + cents / 100)).replace(",", " ")
