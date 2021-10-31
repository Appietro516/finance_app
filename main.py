import asyncio
import os

import finnhub
import websockets

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from websockets import WebSocketClientProtocol

from dotenv import load_dotenv
load_dotenv()

# finnhub_client = finnhub.Client(api_key={os.environ['FINNHUB_KEY']})
# print(finnhub_client.stock_symbols('US'))

app = FastAPI()

html = """

<!DOCTYPE html>

<html>

    <head>

        <title>Chat</title>

    </head>

    <body>

        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">

            <input type="text" id="messageText" autocomplete="off"/>

            <button>Send</button>

        </form>

        <ul id='messages'>

        </ul>

        <script>

            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);

            ws.onmessage = function(event) {

                var messages = document.getElementById('messages')

                var message = document.createElement('li')

                var content = document.createTextNode(event.data)

                message.appendChild(content)

                messages.appendChild(message)

            };

            function sendMessage(event) {

                var input = document.getElementById("messageText")

                ws.send(input.value)

                input.value = ''

                event.preventDefault()

            }

        </script>

    </body>

</html>

"""
class ConnectionManager:
    def __init__(self, bridge = None):
        self.active_connections: List[WebSocket] = []
        if bridge:
            loop = asyncio.get_running_loop()
            loop.create_task(self.reverse(bridge))

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    #recieve input from a websocket and send it to external client
    async def forward(self, ws_a: WebSocket, ws_b: websockets.WebSocketClientProtocol):
        while True:
            data = await ws_a.receive_text()
            print("websocket A received:", data)
            await ws_b.send(data)

    #send websocker external client connection to all
    async def reverse(self, bridge):
        #init ws
        self.ws_b_client = await websockets.connect(bridge)

        #forward connections
        while True:
            data = await manager.ws_b_client.recv()
            for ws_a in manager.active_connections:
                await ws_a.send_text(data)
            print("websocket was A sent:", data)


manager = ConnectionManager(bridge=f"wss://ws.finnhub.io?token={os.environ.get('FINNHUB_KEY')}")



@app.get("/")

async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_a(client_id: int, ws_a: WebSocket):
    print(f"GOT WS {client_id}")
    await manager.connect(ws_a)
    try:
        fwd_task = asyncio.create_task(manager.forward(ws_a, manager.ws_b_client))
        await asyncio.gather(fwd_task)
    except Exception as e:
        print(client_id)
        print(e)
        manager.disconnect(ws_a)


