"""Credit Card Optimization — FastAPI application entry point."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Credit Card Optimization",
    description="The honest Canadian credit card combination optimizer.",
)

# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index() -> dict[str, str]:
    """Placeholder — will be replaced by the input page template."""
    return {"status": "ok", "message": "Credit Card Optimization — scaffold is running."}
