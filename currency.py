import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta


async def get_bank_curses(session, date):
    param = date.strftime("%d.%m.%Y")
    print(f'Loading {param}')
    url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={param}"

    async with session.get(url=url) as response:
        response_text = await response.json()

    return response_text


async def gather_curses(dates: list):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for date in dates:
            task = asyncio.create_task(get_bank_curses(session, date))
            tasks.append(task)

        result = await asyncio.gather(*tasks)
        return result


def get_result_curses(exchangerate: list, currencies: list):
    result = {}
    for curses in exchangerate:
        currency = curses['currency']
        if currency in currencies:
            sales = curses.get('saleRate', None)
            purchase = curses.get('purchaseRate', None)

            result[currency] = {'sale': sales, 'purchase': purchase}
    return result


def get_curses(count_days = 1):
    dates = []
    currency = ['EUR', 'USD']
    result_curses = {}

    if count_days > 10:
        count_days = 10

    start_date = datetime.now().date()
    for i in range(count_days):
        dates.append(start_date - timedelta(days=i))

    result = asyncio.run(gather_curses(dates))

    for data_day in result:
        result_curses[data_day['date']] = get_result_curses(data_day['exchangeRate'], currency)

    return result_curses
