from playwright.sync_api import Page, expect

from configs.config import BASE_URL


def test_ui_logout(logged_in_page):
    """E2E-006：已登录用户退出后应回到登录页并清除 Token。"""

    page = logged_in_page

    # 打开左下角用户菜单
    page.get_by_test_id("user-menu").click()

    # 点击 Log Out
    page.get_by_role(
        "menuitem",
        name="Log Out",
        exact=True,
    ).click()

    # 应跳回登录页
    expect(page).to_have_url(
        f"{BASE_URL}/login"
    )

    # localStorage 中的 JWT 应被清除
    token = page.evaluate(
        "() => localStorage.getItem('access_token')"
    )

    assert token is None


def test_unauthenticated_user_redirected_from_items(page: Page):
    """E2E-007：未登录用户访问 /items 时应跳转到登录页。"""

    page.goto(f"{BASE_URL}/items")

    expect(page).to_have_url(
        f"{BASE_URL}/login"
    )

    expect(
        page.get_by_role(
            "heading",
            name="Login to your account",
            exact=True,
        )
    ).to_be_visible()