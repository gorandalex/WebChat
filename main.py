import asyncio
import aiofile
import aiopath
import currency
import concurrent.futures
from datetime import datetime
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            message = await self.check_message(message)
            await self.send_to_clients(f"{ws.name}: {message}")
            
    async def check_message(self, message):
        if message.strip().startswith('exchange'):
            params = message.split(' ')
            if len(params) > 1:
                try:
                    count_days = int(params[1])
                except ValueError:
                    message = 'Введіть кількість днів (не більше 10)'
            else:
                count_days = 1
                
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [self.run_get_curses(executor, count_days)]
                message = await asyncio.gather(*futures)
            
            await self.log_exchange()
            
        return message
    
    async def run_get_curses(self, executor, count_days):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, currency.get_curses, count_days)
        return result      
                
    async def log_exchange(self):
        apath = aiopath.AsyncPath("log_exchange.txt")
        if not await apath.exists():
            await apath.touch(exist_ok=True)
        async with aiofile.async_open(apath, 'a+') as afp:
            await afp.write(f'{datetime.now().isoformat()}\n')        
        print('Log was written')


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 5000):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
