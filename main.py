import asyncio
import logging
import time
import traceback
import uuid
from asyncio import Queue
from collections import defaultdict
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from uvicorn.config import LOGGING_CONFIG

from model.WxPusher import WxPusher
from settings import SEND_DELAY

logger = logging.getLogger("uvicorn")
format_str = '%(asctime)s [%(levelname)s] %(message)s'
formatter = logging.Formatter(format_str)
LOGGING_CONFIG["formatters"]["default"]["fmt"] = format_str
LOGGING_CONFIG["formatters"]["access"][
    "fmt"] = '%(asctime)s [%(levelname)s] %(client_addr)s - "%(request_line)s" %(status_code)s'

main_queue = Queue()
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
    await main_queue.put(data)
    return {"code": 0, "msg": "ok", "data": {
        "size": main_queue.qsize()
    }}


async def msg_consume():
    logger.info("Start msg consume")
    start = 0
    while True:
        message = await main_queue.get()
        if (remain := SEND_DELAY - (time.time() - start)) > 0:
            await asyncio.sleep(remain)
        start = time.time()
        try:
            # 向后端服务器发送请求
            response = await pusher.send(message)
            logger.info(f"Send msg consume response: {response}")
        except Exception as e:  # noqa
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
