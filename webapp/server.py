import asyncio
import datetime
import functools
import json
import logging
import time

import yaml
import sqlalchemy as sa

from aiohttp import client
from aiohttp import web
from aiopg import sa as aiopg_sa
from sqlalchemy.dialects.postgresql import dml as sa_psql

import webapp.config as config
import webapp.getter_parser as gp
from webapp import validator

logger = logging.getLogger()

logger.setLevel(config.LOGGING_LEVEL)

metadata = sa.MetaData()

tbl = sa.Table(
    "posts",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("url", sa.Text, unique=True),
    sa.Column("title", sa.Text, unique=True),
    sa.Column("created_at", sa.DateTime, server_default=sa.FetchedValue()),
)


def default_json(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    raise TypeError("Unable to serialize {!r}".format(obj))


json_dumps = functools.partial(json.dumps, default=default_json)


async def set_db(app):
    app["pg_engine"] = await aiopg_sa.create_engine(config.POSTGRES_CONNECT_URL)


async def dispose_aiopg(app):
    app["pg_engine"].close()
    await app["pg_engine"].wait_closed()


async def load_schema(app):
    with open(config.YAML_SCHEMA_PATH) as schema:
        sch = yaml.load(schema, Loader=yaml.FullLoader)
        app["schema"] = sch["paths"]


async def set_client(app):
    app["client"] = client.ClientSession()


async def set_updater(app):

    app["feed_queue"] = asyncio.Queue(maxsize=10000)
    app["db_update_event"] = asyncio.Event()

    app["beat"] = asyncio.create_task(beat(app))
    app["worker"] = asyncio.create_task(worker(app))


async def cleanup_updater(app):
    app["beat"].cancel()
    await app["beat"]

    app["worker"].cancel()
    await app["worker"]

    await app["client"].close()


async def get_records_from_db(db, order, limit, offset, descending):
    query = tbl.select()

    if descending:
        query = query.order_by(sa.desc(order))
    else:
        query = query.order_by(order)

    records = []
    query = query.offset(offset).limit(limit)

    async with db.acquire() as conn:
        async for record in conn.execute(query):
            records.append(dict(record))

    return records


async def get_posts(request):

    params = request.query

    order = params.get("order", "id")
    limit = int(params.get("limit", str(config.DEFAULT_NUMBER_OF_POSTS_IN_RESPONSE)))
    offset = int(params.get("offset", "0"))
    descending = "descending" in params and params["descending"] == "true"

    force_update = params.get("force_update")

    if force_update == "true":
        await do_force_update(request.app)

    data = await get_records_from_db(
        request.app["pg_engine"], order, limit, offset, descending
    )

    return web.json_response(data=data, dumps=json_dumps)


async def put_news_into_db(news, db):

    async with db.acquire() as conn:
        await conn.execute(
            sa_psql.insert(tbl)
            .values([{"url": url, "title": title} for url, title in news])
            .on_conflict_do_nothing()
        )


async def do_force_update(app):
    timestamp = time.time()
    await app["feed_queue"].put(timestamp)
    await app["db_update_event"].wait()


def eternal_task(func):
    @functools.wraps(func)
    async def wrapper(app):
        state = {}
        while True:
            try:
                await func(app, state)
            except asyncio.CancelledError:
                break

    return wrapper


@eternal_task
async def beat(app, state):
    logging.debug("Beat")
    feed_queue = app["feed_queue"]
    await asyncio.sleep(config.REQUEST_THROTTLE_SECONDS)
    timestamp = time.time()
    await feed_queue.put(timestamp)


@eternal_task
async def worker(app, state):

    client = app["client"]
    db = app["pg_engine"]
    feed_queue = app["feed_queue"]

    db_update_event = app["db_update_event"]
    current = await feed_queue.get()
    if db_update_event.is_set():
        db_update_event.clear()
    if (
        "previous" not in state
        or current - state["previous"] > config.REQUEST_THROTTLE_SECONDS
    ):
        news = await gp.get_news(client)
        await put_news_into_db(news, db)
        state["previous"] = current

    feed_queue.task_done()
    db_update_event.set()


def make_app():
    app = web.Application(middlewares=[validator.schema_validation])
    app.add_routes([web.get("/posts", get_posts)])

    app.on_startup.append(set_db)
    app.on_startup.append(load_schema)
    app.on_startup.append(set_client)
    app.on_startup.append(set_updater)

    app.on_cleanup.append(dispose_aiopg)
    app.on_cleanup.append(cleanup_updater)

    return app


if __name__ == "__main__":
    logging.info(
        f"Starting app with origin {config.HOST_TO_PARSE} and throttle at {config.REQUEST_THROTTLE_SECONDS}s"
    )
    app = make_app()
    web.run_app(app)
