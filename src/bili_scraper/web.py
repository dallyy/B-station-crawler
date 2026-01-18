import os
import time
import json
import logging
from datetime import datetime
import portalocker
import aiosqlite
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from .service import perform_scrape
from .persist import Persist
from .utils import LOCK_PATH, DB_PATH, DEFAULT_OUTPUT_FILE

app = FastAPI(title="Bili Scraper UI")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

logger = logging.getLogger("bili_scraper.web")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup to ensure tables exist."""
    try:
        persist = Persist()
        await persist.init()
        await persist.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Template filter to format unix timestamps
def format_ts_filter(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""

templates.env.filters['format_ts'] = format_ts_filter


@app.get("/api/status")
async def api_status():
    """Return whether a background scrape is currently running."""
    try:
        if not os.path.exists(LOCK_PATH):
            return {"running": False}
        lock = portalocker.Lock(LOCK_PATH, timeout=0)
        lock.acquire()
        lock.release()
        return {"running": False}
    except portalocker.LockException:
        return {"running": True}


@app.get("/")
async def index(request: Request, page: int = 1, per_page: int = 20):
    """Main page with paginated video list from results.json."""
    page = max(1, page)
    offset = (page - 1) * per_page
    
    # Load data from results.json
    if not os.path.exists(DEFAULT_OUTPUT_FILE):
        all_videos = []
        last_run = None
    else:
        try:
            with open(DEFAULT_OUTPUT_FILE, "r", encoding="utf-8") as f:
                all_videos = json.load(f)
        except Exception:
            all_videos = []
        
        # Get last run from database
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute(
                    "SELECT id, started_at, finished_at, status, processed_count, errors "
                    "FROM scrape_runs ORDER BY id DESC LIMIT 1"
                )
                last_run_row = await cur.fetchone()
                
                last_run = (
                    {
                        "id": last_run_row[0],
                        "started_at": last_run_row[1],
                        "finished_at": last_run_row[2],
                        "status": last_run_row[3],
                        "processed_count": last_run_row[4],
                        "errors": last_run_row[5]
                    }
                    if last_run_row else None
                )
        except Exception as e:
            logger.error(f"Failed to query database: {e}")
            last_run = None
    
    # Get pagination
    total = len(all_videos)
    videos = all_videos[offset:offset + per_page]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    pagination = {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "videos": videos,
        "last_run": last_run,
        "pagination": pagination
    })

@app.post("/scrape")
async def start_scrape(request: Request, background_tasks: BackgroundTasks):
    """Start a background scrape operation."""
    try:
        lock = portalocker.Lock(LOCK_PATH, timeout=0)
        lock.acquire()
    except portalocker.LockException:
        raise HTTPException(status_code=409, detail="Scrape already running")

    try:
        body = await request.json()
    except Exception:
        body = {}
    
    mode = body.get('mode', 'recent')

    async def _scrape_task():
        try:
            logger.info(f"Background scrape started mode={mode}")
            await perform_scrape(out_path=DEFAULT_OUTPUT_FILE)
            logger.info("Background scrape finished")
        except Exception:
            logger.exception("Background scrape failed")
        finally:
            try:
                lock.release()
            except Exception:
                pass

    background_tasks.add_task(_scrape_task)
    return {"status": "started", "mode": mode}


@app.post("/api/delete-results")
async def delete_results():
    """Delete/clear the results.json file."""
    try:
        logger.info("Delete results started")
        # Clear results.json
        os.makedirs(os.path.dirname(DEFAULT_OUTPUT_FILE), exist_ok=True)
        with open(DEFAULT_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        logger.info("Results cleared successfully")
        return {"status": "success", "message": "Results cleared"}
    except Exception as e:
        logger.exception("Delete results failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results.json")
async def get_results():
    """Download results as JSON file."""
    if not os.path.exists(DEFAULT_OUTPUT_FILE):
        raise HTTPException(status_code=404, detail="Results not found")
    return FileResponse(
        DEFAULT_OUTPUT_FILE,
        media_type='application/json',
        filename='results.json'
    )
