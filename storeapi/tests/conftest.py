import logging
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

os.environ["ENV_STATE"] = "test"
from storeapi.database import database, user_table
from storeapi.main import app

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user() -> dict:
    user_details = {"email": "test@example.com", "password": "1234"}

    # Create the client directly in this fixture to avoid async dependency issues
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/register", json=user_details)

        query = user_table.select().where(user_table.c.email == user_details["email"])
        user = await database.fetch_one(query)
        user_details["id"] = user.id

        return user_details

@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    query = (
        user_table.update().where(user_table.c.email == registered_user["email"]).values(confirmed=True)
    )
    await database.execute(query)
    return registered_user

@pytest.fixture()
async def logged_in_user(async_client: AsyncClient, confirmed_user: dict) -> str:
    response = await async_client.post("/token", json=confirmed_user)
    return response.json()["access_token"]
