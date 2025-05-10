from contextlib import suppress
from functools import wraps

from loguru import logger
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.messages import BaseContract, Messages
from src.infrastructure.database.services.session import (
    CTX_SESSION,
    get_session,
)
from src.infrastructure.errors import DatabaseError


def transaction(coro):

    @wraps(coro)
    async def inner(*args, **kwargs):
        session: AsyncSession = get_session()
        CTX_SESSION.set(session)

        try:
            result = await coro(*args, **kwargs)
            await session.commit()
            return result
        except DatabaseError as error:
            logger.error(f"Rolling back changes.\n{error}")
            await session.rollback()
            with suppress(IndexError):
                contract = args[0]
                if not isinstance(contract, BaseContract):
                    return

                await Messages.delete(
                    contract.user.chat_id, *contract.state.messages_to_delete
                )

            raise DatabaseError
        except (IntegrityError, PendingRollbackError) as error:
            logger.error(f"Rolling back changes.\n{error}")
            await session.rollback()
        except Exception as error:
            logger.error(f"Rolling back changes.\n{error}")
            await session.rollback()
        finally:
            await session.close()

    return inner
