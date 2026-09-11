import uuid

import requests
from locust import HttpUser, between, events, task


BASE_URL = "http://localhost:8000"

shared_headers = {}
shared_item_id = None


def get_token(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/api/v1/login/access-token",
        data={
            "username": "admin@example.com",
            "password": "changethis",
        },
        timeout=60,
    )

    response.raise_for_status()

    token = response.json().get("access_token")

    if not token:
        raise RuntimeError("access_token not found")

    return token


def create_test_item(base_url: str) -> str:
    payload = {
        "title": f"perf-d-{uuid.uuid4().hex[:12]}",
        "description": "Scenario D cache performance test",
    }

    response = requests.post(
        f"{base_url}/api/v1/items/",
        headers=shared_headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()["id"]


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global shared_item_id

    base_url = environment.host or BASE_URL

    token = get_token(base_url)

    shared_headers.clear()
    shared_headers["Authorization"] = f"Bearer {token}"

    shared_item_id = create_test_item(base_url)

    # Warm-up:
    # Cache ON 时将目标 Item 写入 Redis；
    # Cache OFF 时只是普通数据库查询。
    response = requests.get(
        f"{base_url}/api/v1/items/{shared_item_id}",
        headers=shared_headers,
        timeout=60,
    )

    response.raise_for_status()

    print(
        f"[Scenario D] Target item prepared: "
        f"{shared_item_id}"
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global shared_item_id

    if not shared_item_id:
        return

    base_url = environment.host or BASE_URL

    requests.delete(
        f"{base_url}/api/v1/items/{shared_item_id}",
        headers=shared_headers,
        timeout=60,
    )

    shared_item_id = None

    print("[Scenario D] Test item cleaned.")


class CacheGetUser(HttpUser):
    wait_time = between(0, 0)

    @task
    def get_cached_item(self):
        if not shared_item_id:
            return

        with self.client.get(
            f"/api/v1/items/{shared_item_id}",
            headers=shared_headers,
            name="D01 GET /items/{id}",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"GET item failed: "
                    f"status={response.status_code}"
                )
                return

            try:
                body = response.json()
            except ValueError:
                response.failure(
                    "Response is not valid JSON"
                )
                return

            if body.get("id") != shared_item_id:
                response.failure(
                    "Returned item id does not match"
                )
                return

            response.success()