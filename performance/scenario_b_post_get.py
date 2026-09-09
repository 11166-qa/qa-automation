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

TEST_PREFIX = "perf-b-"

# 所有虚拟用户共享的认证请求头
shared_headers = {}


def cleanup_performance_data():
    """
    删除场景 B 产生的性能测试数据。

    只删除 title 以 perf-b- 开头的 Item，
    不影响正常业务数据和其他测试数据。
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


def get_shared_token():
    """
    整轮压测开始前只登录一次，
    获取管理员 JWT。
    """

    response = requests.post(
        f"{BASE_URL}/api/v1/login/access-token",
        data={
            "username": "admin@example.com",
            "password": "changethis",
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Performance test login failed: "
            f"{response.status_code} {response.text}"
        )

    body = response.json()

    token = body.get("access_token")

    if not token:
        raise RuntimeError(
            "Performance test login response "
            "does not contain access_token"
        )

    return token


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    每轮压测正式开始前：

    1. 清除上一轮残留的 perf-b-* 数据；
    2. 登录一次；
    3. 为所有虚拟用户准备共享 JWT。
    """

    cleanup_performance_data()

    token = get_shared_token()

    shared_headers.clear()

    shared_headers["Authorization"] = (
        f"Bearer {token}"
    )

    print(
        "[Scenario B] "
        "Old performance data cleaned."
    )

    print(
        "[Scenario B] "
        "Shared authentication token created."
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    本轮压测结束后自动清理性能测试数据。
    """

    cleanup_performance_data()

    print(
        "[Scenario B] "
        "Performance data cleaned after test."
    )


class BusinessUser(HttpUser):
    """
    场景 B：

    已认证用户持续执行：

        POST /items
              ↓
        GET /items/{id}

    本场景只评价创建 + 单条查询的业务性能，
    不把并发登录性能混入统计。
    """

    wait_time = between(0.5, 1.5)

    @task
    def create_and_get_item(self):
        unique_id = uuid.uuid4().hex[:12]

        payload = {
            "title": f"{TEST_PREFIX}{unique_id}",
            "description": "Locust scenario B",
        }

        # ==================================================
        # 1. POST 创建 Item
        # ==================================================

        with self.client.post(
            "/api/v1/items/",
            json=payload,
            headers=shared_headers,
            name="B01 POST /items",
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
                    "Create item response "
                    "is not valid JSON"
                )
                return

            item_id = body.get("id")

            if not item_id:
                response.failure(
                    "Create item response "
                    "does not contain item id"
                )
                return

            if body.get("title") != payload["title"]:
                response.failure(
                    "Created item title "
                    "does not match request"
                )
                return

            response.success()

        # ==================================================
        # 2. GET 查询刚创建的 Item
        # ==================================================

        with self.client.get(
            f"/api/v1/items/{item_id}",
            headers=shared_headers,
            name="B02 GET /items/{id}",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    "Get item failed: "
                    f"status={response.status_code}"
                )
                return

            try:
                body = response.json()
            except ValueError:
                response.failure(
                    "Get item response "
                    "is not valid JSON"
                )
                return

            if body.get("id") != item_id:
                response.failure(
                    "Returned item id "
                    "does not match created item"
                )
                return

            if body.get("title") != payload["title"]:
                response.failure(
                    "Returned item title "
                    "does not match created item"
                )
                return

            response.success()