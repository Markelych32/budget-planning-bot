class AccessForbiden(Exception):
    def __init__(self) -> None:
        return super().__init__("🔐 Доступ запрещён")


class NotFound(Exception):
    def __init__(self, message: str = "") -> None:
        return super().__init__(f"Не найдено: {message}")


class DatabaseError(Exception):
    def __init__(self) -> None:
        return super().__init__("Что-то пошло не так.\n🏋️Попробуйте ещё раз")


class DeprecatedMessage(Exception):
    def __init__(self) -> None:
        return super().__init__("⚠️ Это сообщение устарело")


class ValidationError(Exception):
    def __init__(self, message: str) -> None:
        return super().__init__(f"Ошибка валидации: {message}")


class UserError(Exception):
    def __init__(self, message: str) -> None:
        return super().__init__(message)
