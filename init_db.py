import asyncio
import logging
from bili_scraper.persist import Persist

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing database...")
    persist = Persist()
    await persist.init()
    await persist.close()
    logger.info("Database initialization completed successfully")

if __name__ == '__main__':
    asyncio.run(main())
