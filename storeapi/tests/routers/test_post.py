import pytest
from httpx import AsyncClient
from storeapi import security


async def create_post(body: str, async_client: AsyncClient, logged_in_user: str) -> dict:
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_user}"}
    )
    return response.json()

async def create_comment(body: str, post_id: int, async_client: AsyncClient, logged_in_user: str) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_user}"}
    )
    return response.json()



@pytest.fixture()
async def created_post(body:str, async_client: AsyncClient, logged_in_user: str):
    response = await async_client.post(
        "/post", 
        json={"body": body}, 
        headers={"Authorization": f"Bearer {logged_in_user}"}
        )
    return response.json()

@pytest.fixture()
async def created_comment(body: str, post_id:int, async_client: AsyncClient, logged_in_user: str) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_user}"}
    )
    return response.json()


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, confirmed_user:dict, logged_in_user: str):
    body = "Test Post"
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_user}"}
    )
    assert response.status_code == 201
    assert {"id": 1, "body": "Test Post", "user_id":confirmed_user["id"]}.items() <= response.json().items()

@pytest.mark.anyio
async def test_create_post_expired_token(async_client: AsyncClient, confirmed_user: dict, mocker):
    # mocker function sets the return value of any function to ur desired value for this instance and you should pass the whole path of the function to it
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)  # Set token to expire immediately
    token = security.create_access_token(confirmed_user["email"])
    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

@pytest.mark.anyio
async def test_create_post_missing_data(async_client: AsyncClient, logged_in_user: str):
    response = await async_client.post(
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_user}"}
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")
    assert response.status_code == 200
    assert response.json() == [created_post]


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
    confirmed_user: dict,
):
    body = "Test Comment"

    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"]
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")
    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")
    assert response.status_code == 200
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get("/post/2")
    assert response.status_code == 404
