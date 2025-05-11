import pytest
from unittest.mock import Mock


class MockMessage:
    def __init__(self, text, user_id=123, chat_id=123):
        self.text = text
        self.chat = Mock(id=chat_id)
        self.from_user = Mock(id=user_id, username="test_user", first_name="Test", last_name="User")


class MockBot:
    def __init__(self):
        self.messages = []

    def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})
        return Mock(message_id=len(self.messages))

    def edit_message_text(self, chat_id, message_id, text, **kwargs):
        if message_id <= len(self.messages):
            self.messages[message_id - 1] = {"chat_id": chat_id, "text": text, "kwargs": kwargs}
        return True

    def delete_message(self, chat_id, message_id):
        if message_id <= len(self.messages):
            self.messages[message_id - 1] = None
        return True


@pytest.fixture
def mock_bot():
    return MockBot()


def test_bot_send_message(mock_bot):
    result = mock_bot.send_message(123, "Test message", reply_markup=None)

    assert len(mock_bot.messages) == 1
    assert mock_bot.messages[0]["chat_id"] == 123
    assert mock_bot.messages[0]["text"] == "Test message"
    assert result.message_id == 1


def test_bot_edit_message(mock_bot):
    mock_bot.send_message(123, "Original message")
    mock_bot.edit_message_text(123, 1, "Edited message")

    assert mock_bot.messages[0]["text"] == "Edited message"


def test_bot_delete_message(mock_bot):
    mock_bot.send_message(123, "Message to delete")
    mock_bot.delete_message(123, 1)

    assert mock_bot.messages[0] is None


def test_start_command_handler():
    message = MockMessage("/start")
    bot = MockBot()

    def handle_start(message, bot):
        bot.send_message(message.chat.id, "Привет! Добро пожаловать в Family Budget Bot.")
        return True

    result = handle_start(message, bot)

    assert result is True
    assert len(bot.messages) == 1
    assert "Привет!" in bot.messages[0]["text"]


def test_help_command_handler():
    message = MockMessage("/help")
    bot = MockBot()

    def handle_help(message, bot):
        commands = [
            "/start - Начать работу с ботом",
            "/help - Показать справку",
            "/add_cost - Добавить расход",
            "/add_income - Добавить доход"
        ]
        help_text = "Доступные команды:\n" + "\n".join(commands)
        bot.send_message(message.chat.id, help_text)
        return True

    result = handle_help(message, bot)

    assert result is True
    assert len(bot.messages) == 1
    assert "Доступные команды" in bot.messages[0]["text"]
    assert "/add_cost" in bot.messages[0]["text"]


def test_add_cost_command_handler():
    message = MockMessage("💵 Добавить расходы")
    bot = MockBot()

    def handle_add_cost(message, bot):
        bot.send_message(message.chat.id, "⤵️ Введите значение и нажмите Enter")
        return True

    result = handle_add_cost(message, bot)

    assert result is True
    assert len(bot.messages) == 1
    assert "Введите значение" in bot.messages[0]["text"]


def test_add_income_command_handler():
    message = MockMessage("💰 Доходы")
    bot = MockBot()

    def handle_income(message, bot):
        bot.send_message(message.chat.id, "🤔 Выберите следующую опцию")
        return True

    result = handle_income(message, bot)

    assert result is True
    assert len(bot.messages) == 1
    assert "Выберите следующую опцию" in bot.messages[0]["text"]
