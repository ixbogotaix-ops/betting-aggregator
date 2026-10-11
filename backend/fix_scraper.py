import os

filepath = 'backend/app/capper_scraper.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's clean up the block.
# Find the block starting at '# 2. Пакетно парсим' and ending at 'from .telegram_scraper import process_all_channels_async'
start_marker = '# 2. Пакетно парсим Telegram-каналы (asyncio.gather)'
end_marker = 'from .telegram_scraper import process_all_channels_async'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_block = """        # 2. Парсим кастомные сайты
        from .vprognoze_scraper import scrape_vprognoze
        try:
            await scrape_vprognoze()
        except Exception as e:
            logger.error(f"Error in vprognoze: {e}")

        from .bookmaker_ratings_scraper import scrape_bookmaker_ratings
        try:
            await scrape_bookmaker_ratings()
        except Exception as e:
            logger.error(f"Error in bookmaker_ratings: {e}")

        from .legalbet_scraper import scrape_legalbet
        try:
            await scrape_legalbet()
        except Exception as e:
            logger.error(f"Error in legalbet: {e}")

        from .stavkatv_scraper import scrape_stavkatv
        try:
            await scrape_stavkatv()
        except Exception as e:
            logger.error(f"Error in stavkatv: {e}")

        """
    new_content = content[:start_idx] + new_block + content[end_idx:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed capper_scraper.py")
else:
    print("Could not find markers")
