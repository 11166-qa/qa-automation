import uuid

from playwright.sync_api import expect

from configs.config import BASE_URL


def test_ui_create_item(
    logged_in_page,
    api_client,
    admin_headers,
):
    """E2E-003：通过 UI 创建 Item 并验证页面结果。"""

    page = logged_in_page

    unique_id = uuid.uuid4().hex[:8]

    title = f"e2e-item-{unique_id}"
    description = f"Created by Playwright {unique_id}"

    # 1. 进入 Items 页面
    page.goto(f"{BASE_URL}/items")

    expect(
        page.get_by_role(
            "heading",
            name="Items",
            exact=True,
        )
    ).to_be_visible()

    # 2. 打开新增弹窗
    page.get_by_role(
        "button",
        name="Add Item",
        exact=True,
    ).click()

    dialog = page.get_by_role("dialog")

    expect(dialog).to_be_visible()

    expect(
        dialog.get_by_role(
            "heading",
            name="Add Item",
            exact=True,
        )
    ).to_be_visible()

    # 3. 输入数据
    dialog.get_by_placeholder(
        "Title"
    ).fill(title)

    dialog.get_by_placeholder(
        "Description"
    ).fill(description)

    # 4. 保存
    dialog.get_by_role(
        "button",
        name="Save",
        exact=True,
    ).click()

    # 5. 根据唯一 title 找到对应表格行
    row = page.get_by_role("row").filter(
        has_text=title
    )

    expect(row).to_be_visible()

    # 6. 在这一行中验证 title 和 description
    expect(
        row.get_by_text(
            title,
            exact=True,
        )
    ).to_be_visible()

    expect(
        row.get_by_text(
            description,
            exact=True,
        )
    ).to_be_visible()

    # 7. 获取刚创建 Item 的 ID，用 API 清理测试数据
    items_response = api_client.get_items(
        headers=admin_headers,
    )

    assert items_response.status_code == 200

    items = items_response.json()["data"]

    created_item = next(
        item
        for item in items
        if item["title"] == title
    )

    cleanup_response = api_client.delete_item(
        item_id=created_item["id"],
        headers=admin_headers,
    )

    assert cleanup_response.status_code == 200


def test_ui_update_item(
    logged_in_page,
    api_client,
    admin_headers,
):
    """E2E-004：创建 Item 后，通过 UI 修改并验证结果。"""

    page = logged_in_page

    unique_id = uuid.uuid4().hex[:8]

    original_title = f"e2e-edit-{unique_id}"
    original_description = f"Before update {unique_id}"

    updated_title = f"e2e-updated-{unique_id}"
    updated_description = f"Updated by Playwright {unique_id}"

    # 1. 进入 Items 页面
    page.goto(f"{BASE_URL}/items")

    # 2. 创建测试 Item
    page.get_by_role(
        "button",
        name="Add Item",
        exact=True,
    ).click()

    add_dialog = page.get_by_role("dialog")

    expect(add_dialog).to_be_visible()

    add_dialog.get_by_placeholder(
        "Title"
    ).fill(original_title)

    add_dialog.get_by_placeholder(
        "Description"
    ).fill(original_description)

    add_dialog.get_by_role(
        "button",
        name="Save",
        exact=True,
    ).click()

    # 3. 确认创建成功
    original_row = page.get_by_role(
        "row"
    ).filter(
        has_text=original_title
    )

    expect(original_row).to_be_visible()

    # 4. 打开该 Item 的操作菜单
    original_row.get_by_role(
        "button"
    ).last.click()

    # 5. 点击 Edit Item
    page.get_by_role(
        "menuitem",
        name="Edit Item",
        exact=True,
    ).click()

    # 6. 编辑弹窗
    edit_dialog = page.get_by_role("dialog")

    expect(edit_dialog).to_be_visible()

    expect(
        edit_dialog.get_by_role(
            "heading",
            name="Edit Item",
            exact=True,
        )
    ).to_be_visible()

    edit_dialog.get_by_placeholder(
        "Title"
    ).fill(updated_title)

    edit_dialog.get_by_placeholder(
        "Description"
    ).fill(updated_description)

    edit_dialog.get_by_role(
        "button",
        name="Save",
        exact=True,
    ).click()

    # 7. 根据新标题重新定位更新后的行
    updated_row = page.get_by_role(
        "row"
    ).filter(
        has_text=updated_title
    )

    expect(updated_row).to_be_visible()

    expect(
        updated_row.get_by_text(
            updated_title,
            exact=True,
        )
    ).to_be_visible()

    expect(
        updated_row.get_by_text(
            updated_description,
            exact=True,
        )
    ).to_be_visible()

    # 旧标题应该已经不存在
    expect(
        page.get_by_text(
            original_title,
            exact=True,
        )
    ).to_have_count(0)

    # 8. 用 API 清理更新后的测试 Item
    items_response = api_client.get_items(
        headers=admin_headers,
    )

    assert items_response.status_code == 200

    items = items_response.json()["data"]

    updated_item = next(
        item
        for item in items
        if item["title"] == updated_title
    )

    cleanup_response = api_client.delete_item(
        item_id=updated_item["id"],
        headers=admin_headers,
    )

    assert cleanup_response.status_code == 200


def test_ui_delete_item(
    logged_in_page,
):
    """E2E-005：创建 Item 后，通过 UI 删除并验证记录消失。"""

    page = logged_in_page

    unique_id = uuid.uuid4().hex[:8]

    title = f"e2e-delete-{unique_id}"
    description = f"Delete test item {unique_id}"

    # 1. 进入 Items 页面
    page.goto(f"{BASE_URL}/items")

    # 2. 创建测试 Item
    page.get_by_role(
        "button",
        name="Add Item",
        exact=True,
    ).click()

    add_dialog = page.get_by_role("dialog")

    expect(add_dialog).to_be_visible()

    add_dialog.get_by_placeholder(
        "Title"
    ).fill(title)

    add_dialog.get_by_placeholder(
        "Description"
    ).fill(description)

    add_dialog.get_by_role(
        "button",
        name="Save",
        exact=True,
    ).click()

    # 3. 找到刚创建的 Item 行
    row = page.get_by_role(
        "row"
    ).filter(
        has_text=title
    )

    expect(row).to_be_visible()

    # 4. 打开操作菜单
    row.get_by_role(
        "button"
    ).last.click()

    # 5. 点击 Delete Item
    page.get_by_role(
        "menuitem",
        name="Delete Item",
        exact=True,
    ).click()

    # 6. 删除确认弹窗
    delete_dialog = page.get_by_role(
        "dialog"
    )

    expect(delete_dialog).to_be_visible()

    expect(
        delete_dialog.get_by_role(
            "heading",
            name="Delete Item",
            exact=True,
        )
    ).to_be_visible()

    delete_dialog.get_by_role(
        "button",
        name="Delete",
        exact=True,
    ).click()

    # 7. 验证页面中该 Item 已经不存在
    expect(
        page.get_by_role(
            "row"
        ).filter(
            has_text=title
        )
    ).to_have_count(0)
def test_ui_create_item_empty_title_validation(
    logged_in_page,
):
    """E2E-008：Title 为空时前端应阻止提交并显示校验提示。"""

    page = logged_in_page

    page.goto(f"{BASE_URL}/items")

    page.get_by_role(
        "button",
        name="Add Item",
        exact=True,
    ).click()

    dialog = page.get_by_role("dialog")

    expect(dialog).to_be_visible()

    # 不填写 Title，只填写 Description
    dialog.get_by_placeholder(
        "Description"
    ).fill(
        "Validation test"
    )

    # 点击 Save
    dialog.get_by_role(
        "button",
        name="Save",
        exact=True,
    ).click()

    # 应出现前端校验提示
    expect(
        dialog.get_by_text(
            "Title is required",
            exact=True,
        )
    ).to_be_visible()

    # 弹窗仍应保持打开
    expect(dialog).to_be_visible()