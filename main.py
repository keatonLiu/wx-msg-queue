import asyncio
import uuid
from asyncio import Queue
from dataclasses import field

from fastapi import FastAPI
from pydantic import BaseModel

from model.WxPusher import WxPusher
from settings import SEND_DELAY

app = FastAPI()
main_queue = asyncio.Queue()
msg_queue_map = {}
pusher = WxPusher()


class Msg(BaseModel):
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    content: str
    content_type: int = 2
    url: str = None
    summary: str = None


@app.post("/msg")
async def forward_msg(msg: Msg):
    msg_queue_map[msg.id] = Queue(maxsize=1)
    # 将消息和请求者URL加入队列
    await main_queue.put((msg.id, msg))
    # 阻塞等待响应返回
    response = await msg_queue_map[msg.id].get()
    del msg_queue_map[msg.id]
    return response


async def process_queue():
    while True:
        if not main_queue.empty():
            message_id, message = await main_queue.get()
            try:
                # 向后端服务器发送请求
                response = await pusher.send(message.content, message.content_type, message.url, message.summary)
            except Exception as e:
                response = {"error": str(e)}
            await msg_queue_map[message_id].put(response)

        await asyncio.sleep(SEND_DELAY)


@app.on_event("startup")
async def startup_event():
    # 启动消息处理任务
    await asyncio.create_task(process_queue())


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
