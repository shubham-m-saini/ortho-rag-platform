from fastapi import FastAPI, HTTPException
import os
import sys

# Ensure the app root is in path for service imports
APP_ROOT = os.path.dirname(os.path.dirname(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# Also add services directory explicitly
SERVICES_PATH = os.path.join(APP_ROOT, 'services')
if SERVICES_PATH not in sys.path:
    sys.path.insert(0, SERVICES_PATH)

app = FastAPI(title="Ortho RAG Platform")

# Include routers FIRST (before any service imports that might fail)
from api_gateway.routers import health, discovery, ingestion

app.include_router(health.router)
app.include_router(discovery.router)
app.include_router(ingestion.router)

# Import Services from their isolated folders (lazy import to avoid startup failures)
try:
    from services.discovery_service.src.fetcher import test_youtube_connection 
    DISCOVERY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Discovery service not available at startup: {e}")
    DISCOVERY_AVAILABLE = False

@app.get("/")
def read_root():
    return {"status": "Monolith Ortho Platform Orchestrator Active"}

@app.post("/api/discover")
async def discover_videos(query: str):
    """Orchestrates the discovery flow"""
    try:
        # Call the isolated Discover Service
        videos = await discover_svc.find_videos(query)
        return {"found": len(videos), "videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/{video_id}")
async def process_video(video_id: str):
    """Orchestrates the full RAG pipeline"""
    try:
        # 1. Fetch
        raw_text = await fetcher_svc.get_transcript(video_id)
        
        # 2. Preprocess
        clean_text = preprocess_svc.clean(raw_text)
        
        # 3. Index
        indexer_svc.index(clean_text, video_id)
        
        return {"status": "success", "video_id": video_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
