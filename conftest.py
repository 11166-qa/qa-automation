import os
from pathlib import Path
from utils.redis_client import RedisClient

LOCAL_PLAYWRIGHT_PATH = Path(
    r"D:\P2\playwright-browsers"
)

if os.name == "nt" and LOCAL_PLAYWRIGHT_PATH.exists():
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(LOCAL_PLAYWRIGHT_PATH),
    )
import uuid

import pytest

from configs.config import (
    BASE_URL,
    REQUEST_TIMEOUT,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)
from utils.api_client import APIClient
from utils.db_client import DBClient
from playwright.sync_api import Page
@pytest.fixture(scope="session")
def api_client():
    client = APIClient(
        base_url=BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )

    yield client

    client.close()


@pytest.fixture(scope="session")
def admin_token(api_client):
    response = api_client.login(
        username=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["access_token"]

    return body["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {
        "Authorization": f"Bearer {admin_token}"
    }


@pytest.fixture
def created_item(api_client, admin_headers):
    payload = {
        "title": f"pytest-item-{uuid.uuid4().hex[:8]}",
        "description": "Created automatically by pytest",
    }

    response = api_client.create_item(
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    item = response.json()

    yield item

    cleanup_response = api_client.delete_item(
        item_id=item["id"],
        headers=admin_headers,
    )

    # 如果测试本身已经删除了 Item，
    # teardown 再删除时允许返回 404。
    assert cleanup_response.status_code in (200, 404)


@pytest.fixture
def normal_user(api_client):
    """
    每个需要普通用户的测试：
    1. 自动注册一个唯一测试用户；
    2. 自动登录获取 JWT；
    3. 向测试函数提供用户信息与 headers；
    4. 测试结束自动删除该用户。
    """

    unique_id = uuid.uuid4().hex[:10]

    email = f"pytest-{unique_id}@example.com"
    password = "QaTest12345!"

    signup_response = api_client.post(
        "/api/v1/users/signup",
        json={
            "email": email,
            "password": password,
            "full_name": f"Pytest User {unique_id}",
        },
    )

    assert signup_response.status_code == 200

    user = signup_response.json()

    login_response = api_client.login(
        username=email,
        password=password,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    yield {
        "id": user["id"],
        "email": email,
        "password": password,
        "headers": headers,
    }

    delete_response = api_client.delete(
        "/api/v1/users/me",
        headers=headers,
    )

    assert delete_response.status_code in (200, 401, 404)
@pytest.fixture(scope="session")
def db_client():
    client = DBClient(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    yield client

    client.close()

@pytest.fixture
def logged_in_page(
    page: Page,
):
    page.goto(f"{BASE_URL}/login")

    page.get_by_label(
        "Email",
        exact=True,
    ).fill(ADMIN_EMAIL)

    page.get_by_test_id(
        "password-input"
    ).fill(ADMIN_PASSWORD)

    page.get_by_role(
        "button",
        name="Log In",
        exact=True,
    ).click()

    page.wait_for_url(
        f"{BASE_URL}/"
    )

    return page
@pytest.fixture(scope="session")
def redis_client():
    client = RedisClient()

    assert client.ping() is True

    yield client

    client.close()