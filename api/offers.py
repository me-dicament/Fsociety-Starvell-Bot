import aiohttp
import logging

from api.rate_limiter import throttle


async def create_offer(
    session_cookie: str,
    game_id: int,
    category_id: int,
    price: int,
    quantity: int = 1,
    sid_cookie: str | None = None,
    my_games_cookie: str | None = None,
    title: str | None = None,
    description: str | None = None,
) -> dict:
    """
    Создать новый лот на Starvell.
    Используется для автовосстановления лотов после продажи.
    """
    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://starvell.com",
        "referer": "https://starvell.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36",
    }
    cookies = {"session": session_cookie, "starvell.theme": "dark", "starvell.time_zone": "Europe/Moscow"}
    if my_games_cookie:
        cookies["starvell.my_games"] = my_games_cookie
    if sid_cookie:
        cookies["sid"] = sid_cookie

    payload = {
        "gameId": game_id,
        "categoryId": category_id,
        "price": price,
        "quantity": quantity,
    }
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description

    url = "https://starvell.com/api/offers/create"
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as session:
        await throttle()
        async with session.post(url, json=payload) as resp:
            txt = await resp.text()
            ct = resp.headers.get("Content-Type", "").lower()
            ok = 200 <= resp.status < 300
            parsed = None
            try:
                if "application/json" in ct:
                    parsed = await resp.json()
            except Exception:
                pass
            return {
                "success": ok,
                "status": resp.status,
                "json": parsed or {},
                "raw": (txt or "")[:2000],
            }


async def deactivate_offer(
    session_cookie: str,
    offer_id: int,
    sid_cookie: str | None = None,
    my_games_cookie: str | None = None,
) -> dict:
    """
    Деактивировать лот на Starvell (скрыть, убрать из продажи).
    Используется при отсутствии товара в автовыдаче.
    """
    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://starvell.com",
        "referer": f"https://starvell.com/offers/{offer_id}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36",
    }
    cookies = {"session": session_cookie, "starvell.theme": "dark", "starvell.time_zone": "Europe/Moscow"}
    if my_games_cookie:
        cookies["starvell.my_games"] = my_games_cookie
    if sid_cookie:
        cookies["sid"] = sid_cookie

    payload = {"offerId": offer_id}

    url = "https://starvell.com/api/offers/deactivate"
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as session:
        await throttle()
        async with session.post(url, json=payload) as resp:
            txt = await resp.text()
            ct = resp.headers.get("Content-Type", "").lower()
            ok = 200 <= resp.status < 300
            parsed = None
            try:
                if "application/json" in ct:
                    parsed = await resp.json()
            except Exception:
                pass
            return {
                "success": ok,
                "status": resp.status,
                "json": parsed or {},
                "raw": (txt or "")[:2000],
            }


async def toggle_offer_visibility(
    session_cookie: str,
    offer_id: int,
    sid_cookie: str | None = None,
    my_games_cookie: str | None = None,
) -> dict:
    """
    Переключить видимость лота (вкл/выкл).
    """
    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://starvell.com",
        "referer": f"https://starvell.com/offers/{offer_id}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36",
    }
    cookies = {"session": session_cookie, "starvell.theme": "dark", "starvell.time_zone": "Europe/Moscow"}
    if my_games_cookie:
        cookies["starvell.my_games"] = my_games_cookie
    if sid_cookie:
        cookies["sid"] = sid_cookie

    payload = {"offerId": offer_id}

    url = "https://starvell.com/api/offers/toggle"
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as session:
        await throttle()
        async with session.post(url, json=payload) as resp:
            txt = await resp.text()
            ct = resp.headers.get("Content-Type", "").lower()
            ok = 200 <= resp.status < 300
            parsed = None
            try:
                if "application/json" in ct:
                    parsed = await resp.json()
            except Exception:
                pass
            return {
                "success": ok,
                "status": resp.status,
                "json": parsed or {},
                "raw": (txt or "")[:2000],
            }
