import psycopg

from psycopg.rows import dict_row


class DBClient:
    def __init__(
        self,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ):
        self.connection = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            row_factory=dict_row,
        )

    def fetch_one(
        self,
        sql: str,
        params=None,
    ):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def fetch_all(
        self,
        sql: str,
        params=None,
    ):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute(
        self,
        sql: str,
        params=None,
    ):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)

        self.connection.commit()

    def close(self):
        self.connection.close()