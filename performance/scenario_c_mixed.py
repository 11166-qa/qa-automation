import random
import uuid

import psycopg
import requests
from locust import HttpUser, task, between, events

from configs.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)


BASE_URL = "http://localhost:8000"

TEST_PREFIX = "perf-c-"

# 测试开始前准备一定数量的 Item，
# 供 GET 单条和 UPDATE 任务使用
SEED_ITEM_COUNT = 50

# 所有虚拟用户共享认证信息
shared_headers = {}

# 保存场景 C 中可供查询/更新的 Item ID
shared_item_ids = []


def cleanup_performance_data():
    """
    删除所有场景 C 生成的数据。

    只删除 title 以 perf-c- 开头的 Item，
    不影响其他业务数据。
    """

    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM item
                WHERE title LIKE %s
                """,
                (f"{TEST_PREFIX}%",),
            )

        connection.commit()

    finally:
        connection.close()


def get_shared_token(base_url):
    """
    整轮性能测试开始前只登录一次，
    获取共享 JWT。
    """

    response = requests.post(
        f"{base_url}/api/v1/login/access-token",
        data={
            "username": "admin@example.com",
            "password": "changethis",
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Scenario C login failed: "
            f"{response.status_code} {response.text}"
        )

    token = response.json().get("access_token")

    if not token:
        raise RuntimeError(
            "Scenario C login response "
            "does not contain access_token"
        )

    return token


def create_seed_items(base_url):
    """
    测试正式开始前创建一批种子 Item。

    这些请求不进入 Locust 性能统计，
    只用于给 GET 单条和 UPDATE 提供测试对象。
    """

    shared_item_ids.clear()

    for index in range(SEED_ITEM_COUNT):
        payload = {
            "title": (
                f"{TEST_PREFIX}seed-"
                f"{index}-{uuid.uuid4().hex[:8]}"
            ),
            "description": "Scenario C seed item",
        }

        response = requests.post(
            f"{base_url}/api/v1/items/",
            json=payload,
            headers=shared_headers,
            timeout=60,
        )

        if response.status_code != 200:
            raise RuntimeError(
                "Failed to create seed item: "
                f"{response.status_code} {response.text}"
            )

        item_id = response.json().get("id")

        if not item_id:
            raise RuntimeError(
                "Seed item response does not contain id"
            )

        shared_item_ids.append(item_id)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    每轮测试开始前：

    1. 清理旧测试数据；
    2. 获取共享 JWT；
    3. 创建种子 Item；
    4. 再开始正式混合业务压测。
    """

    base_url = environment.host or BASE_URL

    cleanup_performance_data()

    token = get_shared_token(base_url)

    shared_headers.clear()
    shared_headers["Authorization"] = (
        f"Bearer {token}"
    )

    create_seed_items(base_url)

    print(
        "[Scenario C] Old performance data cleaned."
    )

    print(
        "[Scenario C] Shared token created."
    )

    print(
        f"[Scenario C] "
        f"{len(shared_item_ids)} seed items created."
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试结束后自动清理本轮生成的数据。
    """

    cleanup_performance_data()

    shared_item_ids.clear()

    print(
        "[Scenario C] "
        "Performance data cleaned after test."
    )


class MixedBusinessUser(HttpUser):
    """
    场景 C：登录后的真实混合业务负载。

    权重大致为：

    GET Items 列表       50%
    GET 单个 Item        20%
    POST 创建 Item       20%
    PUT 更新 Item        10%
    """

    wait_time = between(0.5, 1.5)

    # ============================================================
    # C01：查询 Item 列表 —— 50%
    # ============================================================

    @task(5)
    def get_items_list(self):
        with self.client.get(
            "/api/v1/items/",
            params={
                "skip": 0,
                "limit": 50,
            },
            headers=shared_headers,
            name="C01 GET /items",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    "Get items list failed: "
                    f"status={response.status_code}"
                )
                return

            try:
                body = response.json()
            except ValueError:
                response.failure(
                    "Items list response is not JSON"
                )
                return

            if "data" not in body:
                response.failure(
                    "Items list response "
                    "does not contain data"
                )
                return

            response.success()

    # ============================================================
    # C02：查询单个 Item —— 20%
    # ============================================================

    @task(2)
    def get_single_item(self):
        if not shared_item_ids:
            return

        item_id = random.choice(
            shared_item_ids
        )

        with self.client.get(
            f"/api/v1/items/{item_id}",
            headers=shared_headers,
            name="C02 GET /items/{id}",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    "Get single item failed: "
                    f"status={response.status_code}"
                )
                return

            try:
                body = response.json()
            except ValueError:
                response.failure(
                    "Single item response is not JSON"
                )
                return

            if body.get("id") != item_id:
                response.failure(
                    "Returned item id is incorrect"
                )
                return

            response.success()

    # ============================================================
    # C03：创建 Item —— 20%
    # ============================================================

    @task(2)
    def create_item(self):
        unique_id = uuid.uuid4().hex[:12]

        payload = {
            "title": f"{TEST_PREFIX}{unique_id}",
            "description": "Locust scenario C",
        }

        with self.client.post(
            "/api/v1/items/",
            json=payload,
            headers=shared_headers,
            name="C03 POST /items",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    "Create item failed: "
                    f"status={response.status_code}"
                )
                return

            try:
                body = response.json()
            except ValueError:
                response.failure(
                    "Create item response is not JSON"
                )
                return

            item_id = body.get("id")

            if not item_id:
                response.failure(
                    "Create item response "
                    "does not contain id"
                )
                return

            if body.get("title") != payload["title"]:
                response.failure(
                    "Created title does not "
                    "match request"
                )
                return

            shared_item_ids.append(item_id)

            response.success()

    # ============================================================
    # C04：更新 Item —— 10%
    # ============================================================

    @task(1)
    def update_item(self):
        if not shared_item_ids:
            return

        item_id = random.choice(
            shared_item_ids
        )

        unique_id = uuid.uuid4().hex[:8]

        payload = {
            "title": (
                f"{TEST_PREFIX}updated-"
                f"{unique_id}"
            ),
            "description": (
                "Updated by Locust scenario C"
            ),
        }

        with self.client.put(
            f"/api/v1/items/{item_id}",
            json=payload,
            headers=shared_headers,
            name="C04 PUT /items/{id}",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    "Update item failed: "
                    f"status={response.status_code}"
                )
                return

            try:
                body = response.json()
            except ValueError:
                response.failure(
                    "Update response is not JSON"
                )
                return

            if body.get("id") != item_id:
                response.failure(
                    "Updated item id is incorrect"
                )
                return

            if body.get("title") != payload["title"]:
                response.failure(
                    "Updated title does not "
                    "match request"
                )
                return

            response.success()