from playwright.sync_api import Page, expect

from configs.config import BASE_URL


def test_login_page_can_open(page: Page):
    page.goto(f"{BASE_URL}/login")

    expect(
        page.get_by_role(
            "heading",
            name="Login to your account",
        )
    ).to_be_visible()

    expect(
        page.get_by_label(
            "Email",
            exact=True,
        )
    ).to_be_visible()

    expect(
        page.get_by_test_id(
            "password-input"
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "button",
            name="Log In",
            exact=True,
        )
    ).to_be_visible()