import pytest

from configs.config import ADMIN_EMAIL, ADMIN_PASSWORD


def test_login_success(api_client):
    """AUTH-001：正确账号和密码登录成功。"""
    response = api_client.login(
        username=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["access_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.parametrize(
    "username,password",
    [
        (ADMIN_EMAIL, "wrong123"),
        ("nobody@example.com", ADMIN_PASSWORD),
    ],
    ids=[
        "wrong-password",
        "nonexistent-user",
    ],
)
def test_login_invalid_credentials(
    api_client,
    username,
    password,
):
    """AUTH-002~003：账号或密码错误时认证失败。"""
    response = api_client.login(
        username=username,
        password=password,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["detail"] == "Incorrect email or password"


@pytest.mark.parametrize(
    "username,password",
    [
        ("", ADMIN_PASSWORD),
        (ADMIN_EMAIL, ""),
        ("", ""),
    ],
    ids=[
        "empty-username",
        "empty-password",
        "both-empty",
    ],
)
def test_login_empty_fields(
    api_client,
    username,
    password,
):
    """AUTH-004~006：用户名或密码为空字符串时参数校验失败。"""
    response = api_client.login(
        username=username,
        password=password,
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert len(body["detail"]) > 0


def test_login_missing_username(api_client):
    """AUTH-007：完全缺少 username 字段。"""
    response = api_client.post(
        "/api/v1/login/access-token",
        data={
            "password": ADMIN_PASSWORD,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)


def test_login_missing_password(api_client):
    """AUTH-008：完全缺少 password 字段。"""
    response = api_client.post(
        "/api/v1/login/access-token",
        data={
            "username": ADMIN_EMAIL,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)


def test_valid_token(api_client, admin_headers):
    """AUTH-009：有效 Bearer Token 可以访问受保护接口。"""
    response = api_client.post(
        "/api/v1/login/test-token",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == ADMIN_EMAIL
    assert body["is_active"] is True
    assert body["is_superuser"] is True


def test_missing_token(api_client):
    """AUTH-010：缺少 Token 时拒绝访问。"""
    response = api_client.post(
        "/api/v1/login/test-token"
    )

    assert response.status_code == 401


def test_invalid_token(api_client):
    """AUTH-011：非法 Bearer Token 时拒绝访问。"""
    response = api_client.post(
        "/api/v1/login/test-token",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 403


def test_wrong_authorization_scheme(api_client):
    """AUTH-012：错误的认证方案 Basic 不应被当作 Bearer Token 接受。"""
    response = api_client.post(
        "/api/v1/login/test-token",
        headers={
            "Authorization": "Basic invalid-token"
        },
    )

    assert response.status_code == 401