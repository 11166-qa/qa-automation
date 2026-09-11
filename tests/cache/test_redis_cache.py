import uuid

import requests

from configs.config import BASE_URL


def create_test_item(admin_headers):
    unique_id = uuid.uuid4().hex[:10]

    payload = {
        "title": f"redis-test-{unique_id}",
        "description": "Redis automated cache test",
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/items/",
        headers=admin_headers,
        json=payload,
        timeout=10,
    )

    assert response.status_code == 200

    return response.json()


def delete_test_item(admin_headers, item_id):
    response = requests.delete(
        f"{BASE_URL}/api/v1/items/{item_id}",
        headers=admin_headers,
        timeout=10,
    )

    assert response.status_code in (200, 404)


# ============================================================
# CACHE-001 Redis 服务可用
# ============================================================

def test_redis_connection(redis_client):
    assert redis_client.ping() is True


# ============================================================
# CACHE-002 首次 GET 后写入 Redis
# ============================================================

def test_get_item_writes_cache(
    redis_client,
    admin_headers,
):
    item = create_test_item(admin_headers)

    item_id = item["id"]
    cache_key = f"item:{item_id}"

    try:
        redis_client.delete(cache_key)

        assert redis_client.exists(cache_key) is False

        response = requests.get(
            f"{BASE_URL}/api/v1/items/{item_id}",
            headers=admin_headers,
            timeout=10,
        )

        assert response.status_code == 200

        assert redis_client.exists(cache_key) is True

        cached_item = redis_client.get_json(cache_key)

        assert cached_item is not None
        assert cached_item["id"] == item_id
        assert cached_item["title"] == item["title"]
        assert cached_item["description"] == item["description"]

        ttl = redis_client.ttl(cache_key)

        assert 0 < ttl <= 300

    finally:
        redis_client.delete(cache_key)
        delete_test_item(
            admin_headers,
            item_id,
        )


# ============================================================
# CACHE-003 已存在缓存时走 Redis
# ============================================================

def test_get_item_uses_cache(
    redis_client,
    admin_headers,
):
    item = create_test_item(admin_headers)

    item_id = item["id"]
    cache_key = f"item:{item_id}"

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/items/{item_id}",
            headers=admin_headers,
            timeout=10,
        )

        assert response.status_code == 200

        cached_item = redis_client.get_json(cache_key)

        assert cached_item is not None

        # 修改 Redis 中的 title，
        # 但不修改 PostgreSQL。
        # 如果下一次 GET 返回该值，
        # 可以证明请求命中了 Redis。
        cached_item["title"] = "redis-cache-hit"

        redis_client.set_json(
            cache_key,
            cached_item,
            ttl=300,
        )

        response = requests.get(
            f"{BASE_URL}/api/v1/items/{item_id}",
            headers=admin_headers,
            timeout=10,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "redis-cache-hit"

    finally:
        redis_client.delete(cache_key)
        delete_test_item(
            admin_headers,
            item_id,
        )


# ============================================================
# CACHE-004 PUT 后旧缓存失效并重新建立
# ============================================================

def test_update_item_invalidates_cache(
    redis_client,
    admin_headers,
):
    item = create_test_item(admin_headers)

    item_id = item["id"]
    cache_key = f"item:{item_id}"

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/items/{item_id}",
            headers=admin_headers,
            timeout=10,
        )

        assert response.status_code == 200
        assert redis_client.exists(cache_key) is True

        update_payload = {
            "title": "redis-update-test",
            "description": "Updated by Redis cache test",
        }

        response = requests.put(
            f"{BASE_URL}/api/v1/items/{item_id}",
            headers=admin_headers,
            json=update_payload,
            timeout=10,
        )

        assert response.status_code == 200

        # PUT 后旧缓存必须被删除
        assert redis_client.exists(cache_key) is False

        response = requests.get(
            f"{BASE_URL}/api/v1/items/{item_id}",
            headers=admin_headers,
            timeout=10,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "redis-update-test"

        # GET 后重新缓存最新数据
        assert redis_client.exists(cache_key) is True

        cached_item = redis_client.get_json(cache_key)

        assert cached_item["title"] == "redis-update-test"

    finally:
        redis_client.delete(cache_key)
        delete_test_item(
            admin_headers,
            item_id,
        )


# ============================================================
# CACHE-005 DELETE 后缓存失效
# ============================================================

def test_delete_item_invalidates_cache(
    redis_client,
    admin_headers,
):
    item = create_test_item(admin_headers)

    item_id = item["id"]
    cache_key = f"item:{item_id}"

    response = requests.get(
        f"{BASE_URL}/api/v1/items/{item_id}",
        headers=admin_headers,
        timeout=10,
    )

    assert response.status_code == 200

    assert redis_client.exists(cache_key) is True

    response = requests.delete(
        f"{BASE_URL}/api/v1/items/{item_id}",
        headers=admin_headers,
        timeout=10,
    )

    assert response.status_code == 200

    assert redis_client.exists(cache_key) is False

    response = requests.get(
        f"{BASE_URL}/api/v1/items/{item_id}",
        headers=admin_headers,
        timeout=10,
    )

    assert response.status_code == 404