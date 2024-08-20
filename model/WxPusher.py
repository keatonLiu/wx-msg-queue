import aiohttp

from settings import WX_PUSHER_TOKEN, WX_PUSHER_TOPIC

BASEURL = 'http://wxpusher.zjiecode.com/api'


class WxPusher:
    @staticmethod
    async def send(content, content_type=2, url=None, summary=None):
        """Send Message."""
        payload = {
            'appToken': WX_PUSHER_TOKEN,
            'content': content,
            'contentType': content_type,
            'topicIds': [WX_PUSHER_TOPIC],
            'url': url,
            'summary': summary,
        }
        url = f'{BASEURL}/send/message'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()


if __name__ == '__main__':
    WxPusher.send('<h1>这是一条测试消息</h1>')
