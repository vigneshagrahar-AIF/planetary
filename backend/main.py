import sys
import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import time

# Add the current directory (backend) to the Python path explicitly (if needed)
sys.path.append(os.path.dirname(__file__))  # Ensures the current directory is included

# Import your modules after ensuring sys.path is correct
from camera import capture_photo  # Ensure this is correct
from scale_reader import get_weight  # Bluetooth scale handler
from planets import weights_on_planets  # Function to calculate weight on planets
from pdf_maker import create_pdf  # Assuming this function creates a PDF

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Serve static files (images, CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Route for favicon.ico
@app.get("/favicon.ico")
def get_favicon():
    # Path to the favicon.ico file in the 'static' folder
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    return FileResponse(favicon_path)

# Route to serve the root page (index.html)
@app.get("/")
def read_root():
    logger.info("Serving the root page")
    return FileResponse("backend/static/index.html")

# Route to fetch weight in kg and the corresponding weight on planets
@app.get("/get_weight")
async def api_get_weight(weight: float = None):  # Accept manual weight input as a query parameter
    try:
        # Try fetching weight from the scale
        logger.info("Attempting to fetch weight from Bluetooth scale...")
        weight_kg = await get_weight()  # Await the asynchronous function
        logger.info(f"Fetched weight from scale: {weight_kg} kg")
    except Exception as e:
        logger.error(f"Error fetching weight from scale: {e}")
        # If fetching from scale fails, use manual input (if provided)
        if weight is None:
            logger.error("Manual weight not provided, returning error.")
            raise HTTPException(status_code=400, detail="Weight not found and no manual input provided.")
        else:
            weight_kg = weight  # Use manual weight input if scale is not available
            logger.info(f"Using manual weight: {weight_kg} kg")

    # Calculate weight on planets
    planet_weights = weights_on_planets(weight_kg)  # This will calculate weight on planets
    return {"earth_kg": weight_kg, "planets": planet_weights}

# Route to save a photo uploaded by the user
@app.post("/save_photo")
async def api_save_photo(file: UploadFile = File(...)):
    logger.info("Received a photo for upload")
    contents = await file.read()  # Read file content
    path = os.path.join("captures", f"user_{int(time.time())}.jpg")  # Save path
    with open(path, "wb") as f:
        f.write(contents)  # Write file contents
    logger.info(f"Photo saved to {path}")
    return {"path": path}  # Return the path of the saved file

# Route to generate PDF based on payload data
@app.post("/generate_pdf")
async def api_generate_pdf(payload: dict):
    logger.info("Generating PDF from provided payload")
    pdf_path = create_pdf(payload)  # Assuming this function creates a PDF
    logger.info(f"PDF generated at {pdf_path}")
    return FileResponse(pdf_path, filename="space_weight.pdf", media_type="application/pdf")
