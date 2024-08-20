import asyncio
import logging
import uuid
from asyncio import Queue
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.requests import Request

from model.WxPusher import WxPusher
from settings import SEND_DELAY

app = FastAPI()
main_queue = asyncio.Queue()
msg_queue_map = {}
pusher = WxPusher()

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


@app.post("/msg")
async def forward_msg(request: Request):
    data = await request.json()
    msg_id = uuid.uuid4().hex
    msg_queue_map[msg_id] = Queue(maxsize=1)
    # 将消息和请求者URL加入队列
    await main_queue.put((msg_id, data))
    # 阻塞等待响应返回
    response = await msg_queue_map[msg_id].get()
    del msg_queue_map[msg_id]
    return response


async def process_queue():
    logger.info("Start processing queue")
    while True:
        msg_id, message = await main_queue.get()
        try:
            # 向后端服务器发送请求
            response = await pusher.send(message)
        except Exception as e:
            response = {"error": str(e)}
        await msg_queue_map[msg_id].put(response)

        await asyncio.sleep(SEND_DELAY)


@asynccontextmanager
async def lifespan():
    # start background task
    await asyncio.create_task(process_queue())
    yield


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
