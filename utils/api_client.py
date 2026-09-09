import requests


class APIClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, **kwargs):
        return self.session.get(
            self._build_url(path),
            timeout=self.timeout,
            **kwargs,
        )

    def post(self, path: str, **kwargs):
        return self.session.post(
            self._build_url(path),
            timeout=self.timeout,
            **kwargs,
        )

    def put(self, path: str, **kwargs):
        return self.session.put(
            self._build_url(path),
            timeout=self.timeout,
            **kwargs,
        )

    def delete(self, path: str, **kwargs):
        return self.session.delete(
            self._build_url(path),
            timeout=self.timeout,
            **kwargs,
        )

    def login(self, username: str, password: str):
        return self.post(
            "/api/v1/login/access-token",
            data={
                "username": username,
                "password": password,
            },
        )
    def create_item(self, payload: dict, headers: dict):
        return self.post(
            "/api/v1/items/",
            json=payload,
            headers=headers,
        )

    def get_items(self, headers: dict, params: dict | None = None):
        return self.get(
            "/api/v1/items/",
            headers=headers,
            params=params,
        )

    def get_item(self, item_id: str, headers: dict):
        return self.get(
            f"/api/v1/items/{item_id}",
            headers=headers,
        )

    def update_item(self, item_id: str, payload: dict, headers: dict):
        return self.put(
            f"/api/v1/items/{item_id}",
            json=payload,
            headers=headers,
        )

    def delete_item(self, item_id: str, headers: dict):
        return self.delete(
            f"/api/v1/items/{item_id}",
            headers=headers,
        )

    def close(self):
        self.session.close()