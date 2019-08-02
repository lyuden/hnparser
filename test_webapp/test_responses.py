import pytest


async def test_response_format(aiohttp_client, app_fake):

    app = await app_fake()

    client = await aiohttp_client(app)

    resp = await client.get("/posts?force_update=true")

    assert resp.status == 200

    data = await resp.json()

    assert all(("id", "url", "title", "created_at") == tuple(entry) for entry in data)

    entry = data[0]

    assert isinstance(entry["id"], int)

    assert entry["url"].startswith("http://")

    assert " " in entry["title"]


async def test_wrong_parameters(aiohttp_client, app_fake):

    app = await app_fake()
    client = await aiohttp_client(app)

    resp = await client.get("/posts?fdsa=afs")
    assert resp.status == 400

    resp = await client.get("/posts?offset=-1")
    assert resp.status == 400

    resp = await client.get("/posts?limit=-1")
    assert resp.status == 400

    resp = await client.get("/posts?order=fubar")
    assert resp.status == 400

    resp = await client.get("/posts?descending=snafu")
    assert resp.status == 400


@pytest.mark.parametrize("limit", [1, 2, 3, 4, 5])
async def test_limit(aiohttp_client, app_fake, limit):

    app = await app_fake()
    client = await aiohttp_client(app)

    resp = await client.get(f"/posts?limit={limit}&force_update=true")
    assert resp.status == 200
    assert len(await resp.json()) == limit


@pytest.mark.parametrize("offset", [1, 2, 3, 4, 5])
async def test_offset(aiohttp_client, app_fake, offset):

    app = await app_fake()
    client = await aiohttp_client(app)

    resp = await client.get(f"/posts?offset={offset}&force_update=true")
    assert resp.status == 200
    assert len(await resp.json()) == 5 - offset


@pytest.mark.parametrize("order", ["id", "url", "title", "created at"])
async def test_order(aiohttp_client, app_fake, order):

    app = await app_fake()
    client = await aiohttp_client(app)

    resp = await client.get(f"/posts?order={order}&force_update=true&limit=2")
    assert resp.status == 200
    data = await resp.json()
    assert data[0][order] <= data[1][order]


@pytest.mark.parametrize("order", ["id", "url", "title", "created_at"])
async def test_order_descending(aiohttp_client, app_fake, order):

    app = await app_fake()
    client = await aiohttp_client(app)

    resp = await client.get(
        f"/posts?order={order}&force_update=true&limit=2&descending=true"
    )
    assert resp.status == 200
    data = await resp.json()
    assert data[0][order] >= data[1][order]
