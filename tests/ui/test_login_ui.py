from playwright.sync_api import Page, expect

from configs.config import (
    BASE_URL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
)


def test_ui_login_success(page: Page):
    """E2E-001：正确账号密码登录成功。"""

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

    expect(page).to_have_url(
        f"{BASE_URL}/"
    )


def test_ui_login_wrong_password(page: Page):
    """E2E-002：密码错误时仍停留在登录页。"""

    page.goto(f"{BASE_URL}/login")

    page.get_by_label(
        "Email",
        exact=True,
    ).fill(ADMIN_EMAIL)

    page.get_by_test_id(
        "password-input"
    ).fill("wrong12345")

    page.get_by_role(
        "button",
        name="Log In",
        exact=True,
    ).click()

    expect(page).to_have_url(
        f"{BASE_URL}/login"
    )

    expect(
        page.get_by_text(
            "Incorrect email or password",
            exact=True,
        )
    ).to_be_visible()