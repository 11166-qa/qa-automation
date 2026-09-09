import uuid


def test_create_item_persisted_in_database(
    api_client,
    admin_headers,
    db_client,
):
    """DB-001：API 创建 Item 后，数据库中应存在完全对应的记录。"""

    payload = {
        "title": f"db-create-{uuid.uuid4().hex[:8]}",
        "description": "Database consistency test",
    }

    response = api_client.create_item(
        payload=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    api_item = response.json()

    db_item = db_client.fetch_one(
        """
        SELECT
            id,
            title,
            description,
            owner_id
        FROM item
        WHERE id = %s
        """,
        (api_item["id"],),
    )

    assert db_item is not None

    assert str(db_item["id"]) == api_item["id"]
    assert db_item["title"] == payload["title"]
    assert db_item["description"] == payload["description"]
    assert str(db_item["owner_id"]) == api_item["owner_id"]

    # 清理测试数据
    delete_response = api_client.delete_item(
        item_id=api_item["id"],
        headers=admin_headers,
    )

    assert delete_response.status_code == 200
def test_update_item_persisted_in_database(
    api_client,
    admin_headers,
    db_client,
    created_item,
):
    """DB-002：API 更新 Item 后，数据库字段应同步更新。"""

    new_title = f"db-updated-{uuid.uuid4().hex[:8]}"
    new_description = "Updated through API"

    response = api_client.update_item(
        item_id=created_item["id"],
        payload={
            "title": new_title,
            "description": new_description,
        },
        headers=admin_headers,
    )

    assert response.status_code == 200

    db_item = db_client.fetch_one(
        """
        SELECT
            title,
            description
        FROM item
        WHERE id = %s
        """,
        (created_item["id"],),
    )

    assert db_item is not None

    assert db_item["title"] == new_title
    assert db_item["description"] == new_description
def test_delete_item_removed_from_database(
    api_client,
    admin_headers,
    db_client,
    created_item,
):
    """DB-003：API 删除 Item 后，数据库中应不存在该记录。"""

    item_id = created_item["id"]

    response = api_client.delete_item(
        item_id=item_id,
        headers=admin_headers,
    )

    assert response.status_code == 200

    db_item = db_client.fetch_one(
        """
        SELECT id
        FROM item
        WHERE id = %s
        """,
        (item_id,),
    )

    assert db_item is None
def test_normal_user_item_owner_consistency(
    api_client,
    normal_user,
    db_client,
):
    """DB-004：普通用户创建 Item 后，数据库 owner_id 应与当前用户一致。"""

    payload = {
        "title": f"owner-check-{uuid.uuid4().hex[:8]}",
        "description": "Owner consistency test",
    }

    response = api_client.create_item(
        payload=payload,
        headers=normal_user["headers"],
    )

    assert response.status_code == 200

    api_item = response.json()

    db_item = db_client.fetch_one(
        """
        SELECT
            id,
            owner_id
        FROM item
        WHERE id = %s
        """,
        (api_item["id"],),
    )

    assert db_item is not None

    assert str(db_item["owner_id"]) == normal_user["id"]
    assert str(db_item["owner_id"]) == api_item["owner_id"]