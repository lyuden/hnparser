import logging
import aiohttp
import bs4
from webapp import config

logger = logging.getLogger(__name__)

async def get_news(client):
    logging.debug("Starting request")

    async with client.get(config.HOST_TO_PARSE) as resp:

        logging.debug(f'Got response with status {resp.status}')
        html = await resp.text()
        soup = bs4.BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', class_='storylink')

        return [(link['href'], link.text) for link in links]


