import os
from aiopg import sa as aiopg_sa
import asyncio

POSTGRES_CONNECT_URL = os.getenv("POSTGRES_CONNECT_URL", "postgresql://postgres:pass@db:5432/postgres")

print(f'POSTGRES_CONNECT_URL IS {POSTGRES_CONNECT_URL}')

CREATE_TABLE = """
CREATE TABLE posts (
id SERIAL PRIMARY KEY,
url TEXT UNIQUE,
title TEXT UNIQUE,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

async def main():

    engine = await aiopg_sa.create_engine(POSTGRES_CONNECT_URL)

    async with engine.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS posts")
        await conn.execute(CREATE_TABLE)


if __name__ == '__main__':
    asyncio.run(main())
