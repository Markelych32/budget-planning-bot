from datetime import date, timedelta
from functools import partial
from random import randint
from typing import Callable

from src.domain.costs import Cost, CostInDB, CostsCRUD
from src.domain.dates import DateFormat


async def test_filter_for_delete(create_user, create_cost):
    costs_crud = CostsCRUD()
    user = await create_user("john")
    today = date.today()
    month_payload = today.strftime(DateFormat.MONTHLY)
    # Callback that returns the date which is 40-100 days back
    create_past_date: Callable[[], date] = (  # noqa: E731
        lambda: today - partial(timedelta, days=randint(40, 100))()
    )
    # Past costs
    await create_cost(user_id=user.id, category_id=1, date_=create_past_date())
    await create_cost(user_id=user.id, category_id=2, date_=create_past_date())
    # Current month costs
    await create_cost(user_id=user.id, category_id=2)
    cost_in_db: CostInDB = await create_cost(user_id=user.id, category_id=1)

    costs = [
        cost
        async for cost in costs_crud.filter_for_delete(
            month=month_payload, category_id=1
        )
    ]

    expected_cost: Cost = await costs_crud.get(cost_in_db.id)

    assert costs == [expected_cost]
