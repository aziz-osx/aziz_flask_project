from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os
import logging
from reportlab.lib.pagesizes import letter
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler("app.log", maxBytes=10000, backupCount=3)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = Flask(__name__)


data_folder = "data"
if not os.path.exists(data_folder):
    os.makedirs(data_folder)


@app.route("/modify_pdf", methods=["POST"])
def modify_pdf():
    # Check if a file is included in the request
    if "file" not in request.files:
        return "No file part in the request", 400

    file = request.files["file"]
    text_to_write = request.form.get("text", "Default watermark text")

    if file.filename == "":
        return "No file selected for uploading", 400

    if file:
        try:
            input_pdf = PdfReader(file)
            output_pdf = PdfWriter()

            for i, page in enumerate(input_pdf.pages):
                packet = io.BytesIO()
                # Create a new PDF with Reportlab
                can = canvas.Canvas(packet)
                page_width = float(page.mediabox.upper_right[0])
                page_height = float(page.mediabox.upper_right[1])
                can.setPageSize((page_width, page_height))
                
                # Set watermark text properties
                font_size = 20  # Adjust as needed
                can.setFont("Helvetica-Bold", font_size)
                can.setFillColorRGB(0, 0, 0, 0.3)  # Set color and transparency

                # Ensure the watermark is centered
                text_width = can.stringWidth(text_to_write, "Helvetica-Bold", font_size)
                text_x = (page_width - text_width) / 2
                text_y = (page_height - font_size) / 2
                can.saveState()
                can.translate(text_x + text_width / 2, text_y + font_size / 2)
                can.rotate(45)
                can.drawCentredString(0, 0, text_to_write)
                can.restoreState()
                can.save()

                # Move to the beginning of the StringIO buffer
                packet.seek(0)
                new_pdf = PdfReader(packet)
                watermark = new_pdf.pages[0]
                
                # Merge the watermark with the page
                page.merge_page(watermark)
                output_pdf.add_page(page)

            # Save the result
            output_stream = io.BytesIO()
            output_pdf.write(output_stream)
            output_stream.seek(0)

            # Send the result as a file
            return send_file(
                output_stream,
                as_attachment=True,
                download_name="watermarked_file.pdf",
                mimetype="application/pdf",
            )
        except Exception as e:
            # Replace 'app.logger.error' with your actual logging if needed
            print(f"Error processing PDF: {e}")
            return f"An error occurred: {str(e)}", 500

    return "Something went wrong", 500

@app.route("/", methods=["GET"])
def home():
    return "kipic pdf water mark service is active and ready for new siging pdf request. Bon appatit !!"


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error("Server Error: %s", error)
    return str(error), 500


@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error("Unhandled Exception: %s", error)
    return str(error), 500


if __name__ == "__main__":
    app.run(debug=True)
