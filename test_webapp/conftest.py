import datetime

import pytest
from aiopg import sa as aiopg_sa

from webapp import config
from webapp import server

FAKE_RECORDS = [
    ("http://server1", "Title 1"),
    ("http://server2", "Title 2"),
    ("http://server3", "Title 3"),
    ("http://server4", "Title 4"),
    ("http://server5", "A Title 5"),
]

EXAMPLE_HTML = """
<html>
<head></head>
<body>
{}
</body>
</html>
""".format(
    "\n".join(
        f'<a class="storylink" href="{url}">{text}</a>' for url, text in FAKE_RECORDS
    )
)

START = datetime.datetime.fromisoformat("2019-08-02 12:32:55.533172+03:00")

FAKE_RECORDS_DICT = [
    {
        "id": i,
        "url": url,
        "title": title,
        "created_at": str(START + datetime.timedelta(seconds=i + 1)),
    }
    for i, (url, title) in enumerate(FAKE_RECORDS)
]


class FakeResponse:
    def __init__(self, status, content):
        self.status = status
        self.content = content

    async def text(self):
        return self.content


class AsyncContext:
    async def __aenter__(self, *args):
        return FakeResponse(200, EXAMPLE_HTML)

    async def __aexit__(self, *args):
        pass


class FakeClient:
    def get(self, host):
        return AsyncContext()

    async def close(self, *args):
        pass


@pytest.fixture
def fake_client():
    def wrapper():
        return FakeClient()

    return wrapper


@pytest.fixture
async def app_fake(fake_client, monkeypatch):
    async def wrapper():
        async def set_fake_client(app):

            app["client"] = fake_client()

        monkeypatch.setattr(server, "set_client", set_fake_client)
        monkeypatch.setattr(
            config, "POSTGRES_CONNECT_URL", config.TEST_POSTGRES_CONNECT_URL
        )

        engine = await aiopg_sa.create_engine(config.TEST_POSTGRES_CONNECT_URL)
        with open("psql/db_init.psql") as fp:
            query = fp.read()

        async with engine.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS posts")
            await conn.execute(query)

        app = server.make_app()
        return app

    return wrapper
