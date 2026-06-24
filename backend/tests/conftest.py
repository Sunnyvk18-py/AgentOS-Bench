import asyncio

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from app.database import create_all_tables

    asyncio.run(create_all_tables())
    yield
