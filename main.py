import asyncio
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
    while True:
        if not main_queue.empty():
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
