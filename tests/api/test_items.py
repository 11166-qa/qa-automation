import uuid

import pytest


def test_create_item_success(api_client, admin_headers):
    """ITEM-001：正常创建 Item。"""
    payload = {
        "title": f"new-item-{uuid.uuid4().hex[:8]}",
        "description": "API automation test",
    }

    response = api_client.create_item(
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == payload["title"]
    assert body["description"] == payload["description"]
    assert "id" in body
    assert body["id"]
    assert "owner_id" in body
    assert body["owner_id"]

    # 主动清理测试数据
    delete_response = api_client.delete_item(
        item_id=body["id"],
        headers=admin_headers,
    )
    assert delete_response.status_code == 200


def test_get_item_success(
    api_client,
    admin_headers,
    created_item,
):
    """ITEM-002：根据 ID 查询已存在 Item。"""
    response = api_client.get_item(
        item_id=created_item["id"],
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created_item["id"]
    assert body["title"] == created_item["title"]
    assert body["description"] == created_item["description"]


def test_get_items_success(
    api_client,
    admin_headers,
    created_item,
):
    """ITEM-003：查询 Item 列表。"""
    response = api_client.get_items(
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert "data" in body
    assert "count" in body
    assert isinstance(body["data"], list)
    assert isinstance(body["count"], int)

    item_ids = [
        item["id"]
        for item in body["data"]
    ]

    assert created_item["id"] in item_ids


def test_update_item_success(
    api_client,
    admin_headers,
    created_item,
):
    """ITEM-004：正常更新 Item。"""
    new_title = f"updated-{uuid.uuid4().hex[:8]}"

    payload = {
        "title": new_title,
        "description": "Updated by pytest",
    }

    response = api_client.update_item(
        item_id=created_item["id"],
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created_item["id"]
    assert body["title"] == new_title
    assert body["description"] == "Updated by pytest"


def test_delete_item_success(
    api_client,
    admin_headers,
    created_item,
):
    """ITEM-005：正常删除 Item。"""
    item_id = created_item["id"]

    response = api_client.delete_item(
        item_id=item_id,
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == "Item deleted successfully"

    # 删除后再次查询，应不存在
    get_response = api_client.get_item(
        item_id=item_id,
        headers=admin_headers,
    )

    assert get_response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "",
            "description": "empty title",
        },
        {
            "title": "A" * 256,
            "description": "title too long",
        },
        {
            "title": "valid title",
            "description": "A" * 256,
        },
    ],
    ids=[
        "empty-title",
        "title-too-long",
        "description-too-long",
    ],
)
def test_create_item_invalid_fields(
    api_client,
    admin_headers,
    payload,
):
    """ITEM-006~008：创建 Item 时字段长度不合法。"""
    response = api_client.create_item(
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)


def test_create_item_missing_title(
    api_client,
    admin_headers,
):
    """ITEM-009：创建时完全缺少 title。"""
    payload = {
        "description": "missing title",
    }

    response = api_client.create_item(
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_get_nonexistent_item(
    api_client,
    admin_headers,
):
    """ITEM-010：查询不存在的合法 UUID。"""
    nonexistent_id = str(uuid.uuid4())

    response = api_client.get_item(
        item_id=nonexistent_id,
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Item not found"


def test_get_item_invalid_uuid(
    api_client,
    admin_headers,
):
    """ITEM-011：ID 不是合法 UUID。"""
    response = api_client.get_item(
        item_id="not-a-valid-uuid",
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_create_item_without_token(api_client):
    """ITEM-012：未携带 Token 创建 Item。"""
    payload = {
        "title": "unauthorized-item",
        "description": "should not be created",
    }

    response = api_client.post(
        "/api/v1/items/",
        json=payload,
    )

    assert response.status_code == 401


def test_get_items_without_token(api_client):
    """ITEM-013：未携带 Token 查询列表。"""
    response = api_client.get(
        "/api/v1/items/"
    )

    assert response.status_code == 401
def test_update_nonexistent_item(
    api_client,
    admin_headers,
):
    """ITEM-014：更新不存在的合法 UUID。"""

    nonexistent_id = str(uuid.uuid4())

    response = api_client.update_item(
        item_id=nonexistent_id,
        payload={
            "title": "updated-title",
        },
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Item not found"
def test_delete_nonexistent_item(
    api_client,
    admin_headers,
):
    """ITEM-015：删除不存在的合法 UUID。"""

    nonexistent_id = str(uuid.uuid4())

    response = api_client.delete_item(
        item_id=nonexistent_id,
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Item not found"
@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "",
        },
        {
            "title": "A" * 256,
        },
        {
            "description": "A" * 256,
        },
    ],
    ids=[
        "empty-title",
        "title-too-long",
        "description-too-long",
    ],
)
def test_update_item_invalid_fields(
    api_client,
    admin_headers,
    created_item,
    payload,
):
    """ITEM-016~018：更新 Item 时字段长度非法。"""

    response = api_client.update_item(
        item_id=created_item["id"],
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)
def test_normal_user_create_own_item(
    api_client,
    normal_user,
):
    """ITEM-019：普通用户可以创建自己的 Item。"""

    payload = {
        "title": f"user-item-{uuid.uuid4().hex[:8]}",
        "description": "Created by normal user",
    }

    response = api_client.create_item(
        payload=payload,
        headers=normal_user["headers"],
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == payload["title"]
    assert body["owner_id"] == normal_user["id"]

    # 不需要手动删除。
    # normal_user fixture 最终删除用户时会清理其 Item。
def test_normal_user_cannot_get_admin_item(
    api_client,
    normal_user,
    created_item,
):
    """ITEM-020：普通用户不能读取其他用户的 Item。"""

    response = api_client.get_item(
        item_id=created_item["id"],
        headers=normal_user["headers"],
    )

    assert response.status_code == 403

    body = response.json()

    assert body["detail"] == "Not enough permissions"
def test_normal_user_cannot_update_admin_item(
    api_client,
    normal_user,
    created_item,
):
    """ITEM-021：普通用户不能修改其他用户的 Item。"""

    response = api_client.update_item(
        item_id=created_item["id"],
        payload={
            "title": "Unauthorized update",
        },
        headers=normal_user["headers"],
    )

    assert response.status_code == 403

    body = response.json()

    assert body["detail"] == "Not enough permissions"
def test_normal_user_cannot_delete_admin_item(
    api_client,
    normal_user,
    created_item,
):
    """ITEM-022：普通用户不能删除其他用户的 Item。"""

    response = api_client.delete_item(
        item_id=created_item["id"],
        headers=normal_user["headers"],
    )

    assert response.status_code == 403

    body = response.json()

    assert body["detail"] == "Not enough permissions"
def test_normal_user_list_excludes_admin_item(
    api_client,
    normal_user,
    created_item,
):
    """ITEM-023：普通用户列表只能返回自己的 Item。"""

    response = api_client.get_items(
        headers=normal_user["headers"],
    )

    assert response.status_code == 200

    body = response.json()

    item_ids = [
        item["id"]
        for item in body["data"]
    ]

    assert created_item["id"] not in item_ids
def test_admin_can_get_normal_user_item(
    api_client,
    admin_headers,
    normal_user,
):
    """ITEM-024：超级管理员可以读取普通用户创建的 Item。"""

    create_response = api_client.create_item(
        payload={
            "title": f"normal-item-{uuid.uuid4().hex[:8]}",
            "description": "Normal user owned item",
        },
        headers=normal_user["headers"],
    )

    assert create_response.status_code == 200

    item = create_response.json()

    response = api_client.get_item(
        item_id=item["id"],
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == item["id"]
    assert body["owner_id"] == normal_user["id"]