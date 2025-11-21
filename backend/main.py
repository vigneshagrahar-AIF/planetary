import os
import sys
import time
import threading
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# -------------------------------------------------------------------
# PATHS / IMPORTS
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from planets import weights_on_planets
from scale_reader import get_weight  # async stub for now (currently unused)
from pdf_maker import create_pdf

# If you later use this:
# from camera import capture_photo

# -------------------------------------------------------------------
# GLOBAL STATE (for phone/Flutter integration)
# -------------------------------------------------------------------
_latest_weight_kg: Optional[float] = None
_latest_name: Optional[str] = None
_latest_at: Optional[float] = None   # when we last got a weight from the phone
_state_lock = threading.Lock()

# -------------------------------------------------------------------
# FASTAPI APP
# -------------------------------------------------------------------
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("space-weight")

static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# -------------------------------------------------------------------
# BASIC ROUTES
# -------------------------------------------------------------------
@app.get("/favicon.ico")
def get_favicon():
    """Optional favicon support."""
    path = os.path.join(static_dir, "favicon.ico")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No favicon")
    return FileResponse(path)


@app.get("/")
def read_root():
    """Serve the main HTML page."""
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=500, detail="index.html not found in static/")
    return FileResponse(index_path)


# -------------------------------------------------------------------
# PHONE / FLUTTER ENTRY POINT
# -------------------------------------------------------------------
@app.post("/set_weight_from_phone")
async def set_weight_from_phone(request: Request):
    """
    Called by the Flutter/AiLink app.
    Expects JSON: {"name": "ScaleStation1", "weight_kg": 63.4}
    `name` is OPTIONAL (only for logging / debugging).
    """
    data = await request.json()

    name = (data.get("name") or "").strip()
    weight = data.get("weight_kg")

    # name is optional now – only weight is required
    try:
        weight = float(weight)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="weight_kg must be a number")

    if weight <= 0:
        raise HTTPException(status_code=400, detail="weight_kg must be > 0")

    global _latest_weight_kg, _latest_name, _latest_at
    with _state_lock:
        _latest_weight_kg = weight
        # keep the last non-empty name (for debugging)
        if name:
            _latest_name = name
        _latest_at = time.time()

    logger.info(f"[PHONE] Received weight from {name or 'phone-client'}: {weight:.2f} kg")

    return {"status": "ok"}


# -------------------------------------------------------------------
# CORE: /get_weight USED BY YOUR HTML
# -------------------------------------------------------------------
@app.get("/get_weight")
async def api_get_weight(weight: Optional[float] = None):
    """
    Where does weight come from?

    Priority:
    1. If phone sent a RECENT weight via /set_weight_from_phone (<= 30 seconds old), use that.
    2. Else, if ?weight= query given, use that.
    3. Else, error.
    """
    global _latest_weight_kg, _latest_name, _latest_at

    now = time.time()
    with _state_lock:
        cached_weight = _latest_weight_kg
        cached_name = _latest_name
        cached_at = _latest_at

    # Is the cached phone weight fresh enough?
    use_cached = (
        cached_weight is not None
        and cached_at is not None
        and (now - cached_at) <= 30.0   # 30 second freshness window
    )

    if use_cached:
        weight_kg = cached_weight
        name = cached_name
        source = "phone"
        logger.info(f"Using cached phone weight: {weight_kg} kg (fresh)")
    else:
        # 2) Fallback: ?weight= query
        if weight is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No weight available (phone has not sent a recent one "
                    "and no ?weight= provided)."
                ),
            )
        try:
            weight_kg = float(weight)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="?weight must be a number")

        name = None
        source = "query"
        logger.info(f"Using query weight: {weight_kg} kg")

    planet_weights = weights_on_planets(weight_kg)

    return {
        "source": source,        # "phone" or "query"
        "earth_kg": weight_kg,   # number
        "name": name,            # may be null
        "planets": planet_weights
    }


# -------------------------------------------------------------------
# SAVE PHOTO (optional, if you later upload selfie from browser)
# -------------------------------------------------------------------
@app.post("/save_photo")
async def api_save_photo(file: UploadFile = File(...)):
    os.makedirs("captures", exist_ok=True)

    contents = await file.read()
    filename = f"user_{int(time.time())}.jpg"
    path = os.path.join("captures", filename)

    with open(path, "wb") as f:
        f.write(contents)

    logger.info(f"Photo saved to {path}")
    return {"path": path}


# -------------------------------------------------------------------
# GENERATE PDF (optional server-side report)
# -------------------------------------------------------------------
@app.post("/generate_pdf")
async def api_generate_pdf(payload: dict):
    pdf_path = create_pdf(payload)
    logger.info(f"PDF generated at {pdf_path}")
    return FileResponse(
        pdf_path,
        filename="space_weight.pdf",
        media_type="application/pdf",
    )
