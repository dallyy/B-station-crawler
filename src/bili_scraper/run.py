import asyncio
import logging
import sys
import time
import portalocker
from datetime import datetime, timezone
from .service import perform_scrape
from .persist import Persist
from .utils import LOG_DIR, LOCK_PATH, EXIT_SUCCESS, EXIT_PERMANENT_ERROR, EXIT_ALREADY_RUNNING

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler(
            f"{LOG_DIR}/run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("bili_scraper")


async def main(args):
    """Run scraper with arguments."""
    started_at = int(time.time())
    try:
        result = await perform_scrape(
            keywords_file=args.keywords,
            db_path=args.db,
            out_path=args.out
        )
        logger.info(f"Scrape complete: {result['processed']} items, exported to {result['out']}")
        return EXIT_SUCCESS
    except Exception as e:
        logger.exception("Fatal error during run")
        try:
            persist = Persist(db_path=args.db)
            await persist.init()
            await persist.write_run(started_at, int(time.time()), "failed", 0, str(e))
            await persist.close()
        except Exception:
            logger.exception("Failed to record failure in DB")
        return EXIT_PERMANENT_ERROR


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bilibili scraper")
    parser.add_argument("--keywords", help="path to keywords file")
    parser.add_argument("--db", help="path to sqlite db")
    parser.add_argument("--out", help="path to json output file")
    args = parser.parse_args()

    # Acquire lock to prevent concurrent runs
    try:
        lock = portalocker.Lock(LOCK_PATH, timeout=0)
        lock.acquire()
    except portalocker.LockException:
        logger.warning("Another instance is running; exiting")
        sys.exit(EXIT_ALREADY_RUNNING)

    try:
        code = asyncio.run(main(args))
        sys.exit(code)
    finally:
        try:
            lock.release()
        except Exception:
            pass
