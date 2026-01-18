import asyncio
import aiosqlite
from bili_scraper.utils import DB_PATH

async def clear_database():
    """Clear all data from database tables while keeping the structure."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Clear videos table
            cursor1 = await db.execute("DELETE FROM videos")
            videos_deleted = cursor1.rowcount
            
            # Clear scrape_runs table
            cursor2 = await db.execute("DELETE FROM scrape_runs")
            runs_deleted = cursor2.rowcount
            
            # Reset auto-increment sequence
            await db.execute("DELETE FROM sqlite_sequence WHERE name IN ('videos', 'scrape_runs')")
            
            # Commit changes
            await db.commit()
            
            return {
                "videos_deleted": videos_deleted,
                "runs_deleted": runs_deleted,
                "status": "success"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

async def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Clearing database content...")
    result = await clear_database()
    
    if result["status"] == "success":
        logger.info(f"Database cleared successfully:")
        logger.info(f"  - Deleted {result['videos_deleted']} videos")
        logger.info(f"  - Deleted {result['runs_deleted']} scrape runs")
        logger.info(f"  - Reset auto-increment sequences")
    else:
        logger.error(f"Failed to clear database: {result['message']}")

if __name__ == '__main__':
    asyncio.run(main())
