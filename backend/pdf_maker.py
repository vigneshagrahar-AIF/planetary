from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm  # Add this import for cm
from datetime import datetime
from PIL import Image
import os

def create_pdf(data: dict) -> str:
    os.makedirs("pdfs", exist_ok=True)
    filename = datetime.now().strftime("space_weight_%Y%m%d_%H%M%S.pdf")
    pdf_path = os.path.join("pdfs", filename)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, height - 2 * cm, "Your Weight Across the Solar System")

    # Earth weight
    c.setFont("Helvetica", 14)
    earth_text = f"On Earth: {data['earth_kg']:.1f} kg"
    c.drawString(2 * cm, height - 3.5 * cm, earth_text)

    # Planet weights
    y = height - 5 * cm
    for planet, weight in data["planets"].items():
        c.drawString(2 * cm, y, f"{planet}: {weight} kg")
        y -= 0.7 * cm

    # Display photo
    if "photo_path" in data and os.path.exists(data["photo_path"]):
        img = Image.open(data["photo_path"])
        max_width = 8 * cm
        max_height = 8 * cm
        img.thumbnail((max_width, max_height))
        img_temp = os.path.join("pdfs", "temp_photo.jpg")
        img.save(img_temp)
        c.drawImage(img_temp, width - max_width - 2 * cm, 4 * cm, width=max_width, height=max_height)

    c.showPage()
    c.save()
    return pdf_path
