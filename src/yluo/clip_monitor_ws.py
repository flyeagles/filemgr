#!/usr/bin/env python

import asyncio
import datetime
import random
import websockets

import pyperclip
import time

connected = set()

async def monitor_clipboard_send(websocket, path):
    global connected
    connected.add(websocket)

    old_clip = "dummy"
    print("Ready to serve web socket " + path)
    try:
        while True:
            while True:
                clip_text = pyperclip.paste()
                if clip_text != old_clip:
                    old_clip = clip_text
                    if '\n' not in clip_text:
                        break

                time.sleep(0.3)

            print("Send out " + old_clip)
            print(len(connected))
            await asyncio.wait([ws.send(old_clip) for ws in connected])
            # await websocket.send(old_clip)
            # await asyncio.sleep(random.random() * 3)
    finally:
        for ws in connected:
            ws.close()

print("Prepare to start web socket server.")
port = 15678
start_server = websockets.serve(monitor_clipboard_send, '127.0.0.1', port)

asyncio.get_event_loop().run_until_complete(start_server)

print("Server web socket started at port {pt}".format(pt=port))

asyncio.get_event_loop().run_forever()
