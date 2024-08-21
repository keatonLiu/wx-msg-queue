import asyncio
import logging
import time
import traceback
import uuid
from asyncio import Queue
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.requests import Request

from model.WxPusher import WxPusher
from settings import SEND_DELAY

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

main_queue = Queue()
msg_queue_map = defaultdict(lambda: Queue(maxsize=1))
pusher = WxPusher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start background task
    _ = asyncio.create_task(msg_consume())
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/msg")
async def forward_msg(request: Request):
    data = await request.json()
    msg_id = uuid.uuid4().hex
    # 将消息和请求者URL加入队列
    await main_queue.put((msg_id, data))
    # 阻塞等待响应返回
    response = await msg_queue_map[msg_id].get()
    del msg_queue_map[msg_id]
    return response


async def msg_consume():
    logger.info("Start msg consume")
    start = 0
    while True:
        msg_id, message = await main_queue.get()
        if (remain := SEND_DELAY - (time.time() - start)) > 0:
            await asyncio.sleep(remain)
        start = time.time()
        try:
            # 向后端服务器发送请求
            response = await pusher.send(message)
        except Exception as e:
            response = {"code": -1, "error": str(e)}
            logger.error(traceback.format_exc())
        await msg_queue_map[msg_id].put(response)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
