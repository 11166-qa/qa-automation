from locust import HttpUser, task, between, events
import requests


BASE_URL = "http://localhost:8000"

shared_headers = {}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    整轮压测开始前只登录一次，
    获取共享 JWT，避免并发登录干扰 GET 性能测试。
    """
    response = requests.post(
        f"{BASE_URL}/api/v1/login/access-token",
        data={
            "username": "admin@example.com",
            "password": "changethis",
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Performance test login failed: "
            f"{response.status_code} {response.text}"
        )

    token = response.json()["access_token"]

    shared_headers["Authorization"] = (
        f"Bearer {token}"
    )


class GetItemsUser(HttpUser):
    """
    场景 A：
    已认证用户持续执行 GET /items。
    登录阶段不计入并发 GET 性能。
    """

    wait_time = between(0.5, 1.5)

    @task
    def get_items(self):
        with self.client.get(
            "/api/v1/items/",
            headers=shared_headers,
            name="GET /items",
            catch_response=True,
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Unexpected status code: "
                    f"{response.status_code}"
                )