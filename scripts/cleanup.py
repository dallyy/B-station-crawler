import asyncio
import argparse
from bili_scraper.persist import Persist

async def main(retention_days: int = 30, delete: bool = False):
    persist = Persist()
    await persist.init()
    res = await persist.archive_old_videos(retention_days=retention_days, delete_after_archive=delete)
    print('result:', res)
    await persist.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--retention', type=int, default=30)
    parser.add_argument('--delete', action='store_true')
    args = parser.parse_args()
    asyncio.run(main(retention_days=args.retention, delete=args.delete))
