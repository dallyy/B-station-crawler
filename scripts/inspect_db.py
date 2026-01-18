import asyncio
import aiosqlite

async def main():
    db = 'data.sqlite'
    async with aiosqlite.connect(db) as conn:
        cur = await conn.execute('SELECT COUNT(*) FROM videos')
        rows = await cur.fetchone()
        print('videos:', rows[0])
        cur = await conn.execute('SELECT id, started_at, finished_at, status, processed_count, errors FROM scrape_runs ORDER BY id DESC LIMIT 1')
        r = await cur.fetchone()
        print('last_run:', r)

if __name__ == '__main__':
    asyncio.run(main())
