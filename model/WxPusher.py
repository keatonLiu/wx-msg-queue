import aiohttp

BASEURL = 'http://wxpusher.zjiecode.com/api'


class WxPusher:
    @staticmethod
    async def send(payload):
        """Send Message."""
        url = f'{BASEURL}/send/message'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()
