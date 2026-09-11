import json
from typing import Any

from redis import Redis

from configs.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_TIMEOUT,
)


class RedisClient:
    def __init__(self):
        self.client = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=REDIS_TIMEOUT,
            socket_timeout=REDIS_TIMEOUT,
        )

    def ping(self) -> bool:
        return bool(self.client.ping())

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def get(self, key: str) -> str | None:
        return self.client.get(key)

    def get_json(self, key: str) -> dict[str, Any] | None:
        value = self.get(key)

        if value is None:
            return None

        return json.loads(value)

    def set_json(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int = 300,
    ) -> None:
        self.client.set(
            name=key,
            value=json.dumps(value),
            ex=ttl,
        )

    def ttl(self, key: str) -> int:
        return self.client.ttl(key)

    def delete(self, key: str) -> int:
        return self.client.delete(key)

    def close(self) -> None:
        self.client.close()