import asyncio
import logging
import aiohttp
import cloudscraper

logger = logging.getLogger(__name__)

def get_cloudflare_cookies(url: str):
    """
    Добывает cf_clearance и другие обходные куки с помощью cloudscraper.
    Это легковесный способ пройти проверку Cloudflare без запуска реального браузера (Playwright/Camoufox).
    
    Возвращает: (словарь_с_куками, User-Agent)
    """
    logger.info(f"[CF Bypass] Попытка пробить Cloudflare для {url}...")
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True
        }
    )
    
    # Делаем синхронный запрос, чтобы пройти JS-челлендж и получить куки
    response = scraper.get(url)
    
    if response.status_code in [200, 301, 302]:
        logger.info(f"[CF Bypass] ✅ Cloudflare успешно пройден! Статус: {response.status_code}")
        cookies_dict = scraper.cookies.get_dict()
        user_agent = scraper.headers.get("User-Agent")
        return cookies_dict, user_agent
    else:
        logger.warning(f"[CF Bypass] ❌ Не удалось пробить Cloudflare. Статус: {response.status_code}")
        return None, None

async def create_cleared_aiohttp_session(url: str) -> aiohttp.ClientSession:
    """
    Генерирует и возвращает готовую асинхронную сессию aiohttp, 
    которая уже содержит нужные куки для обхода Cloudflare.
    
    Эту сессию можно использовать в парсере Telegram или других модулях 
    для молниеносных асинхронных запросов.
    """
    cookies, user_agent = await asyncio.to_thread(get_cloudflare_cookies, url)
    
    if cookies and user_agent:
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        session = aiohttp.ClientSession(cookies=cookies, headers=headers)
        logger.info("[CF Bypass] Асинхронная сессия aiohttp с clearance-куками создана.")
        return session
    
    logger.error("[CF Bypass] Ошибка создания aiohttp сессии (нет кук). Возвращаем стандартную.")
    return aiohttp.ClientSession()

async def test_cloudflare_bypass(test_url: str = "https://vprognoze.ru/forecast/new/"):
    """
    Тестовая функция для проверки работоспособности модуля.
    Выполняет запрос через "очищенную" aiohttp сессию и выводит результат.
    """
    logger.info(f"[CF Test] Тестируем обход на сайте: {test_url}")
    session = await create_cleared_aiohttp_session(test_url)
    
    try:
        async with session.get(test_url, timeout=15) as response:
            html = await response.text()
            if "Just a moment" in html or "Cloudflare" in html:
                logger.error("[CF Test] ПРОВАЛ: Сработала капча/заглушка Cloudflare.")
            else:
                logger.info(f"[CF Test] УСПЕХ: Получен чистый HTML ({len(html)} байт).")
                logger.info("[CF Test] Заголовок страницы: " + html[html.find('<title>'):html.find('</title>')+8])
    except Exception as e:
        logger.error(f"[CF Test] Ошибка запроса: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_cloudflare_bypass())
