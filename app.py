from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

@app.route('/modify_pdf', methods=['POST'])
def modify_pdf():
    # Check if a file is included in the request
    if 'file' not in request.files:
        return "No file part in the request", 400

    # Extract text from the request JSON, default to a standard text if not provided
    text_to_write = request.form.get('text', 'Default text if not provided')

    file = request.files['file']

    if file.filename == '':
        return "No file selected for uploading", 400

    if file:
        try:
            input_pdf = PdfReader(file)
            output_pdf = PdfWriter()

            for i, page in enumerate(input_pdf.pages):
                # Create an overlay PDF with Reportlab
                overlay_packet = io.BytesIO()
                overlay = canvas.Canvas(overlay_packet)

                # Set the size of the overlay to match the input page
                page_width = float(page.mediabox.upper_right[0])
                page_height = float(page.mediabox.upper_right[1])
                overlay.setPageSize((page_width, page_height))

                # Draw the border and use the provided text
                overlay.setStrokeColorRGB(0, 0, 0)  # Black color
                overlay.setLineWidth(5)
                overlay.rect(5, 5, page_width - 10, page_height - 10)
                overlay.setFont("Helvetica", 12)
                overlay.drawString(30, 30, text_to_write)  # Position the text at the bottom-left
                overlay.save()

                # Move back to the start of the BytesIO object
                overlay_packet.seek(0)
                overlay_pdf = PdfReader(overlay_packet)

                # Merge the overlay with the original page
                page.merge_page(overlay_pdf.pages[0])
                output_pdf.add_page(page)

            # Save the merged PDF to a BytesIO object
            output_stream = io.BytesIO()
            output_pdf.write(output_stream)
            output_stream.seek(0)

            return send_file(
                output_stream,
                as_attachment=True,
                download_name='modified_file.pdf',
                mimetype='application/pdf'
            )

        except Exception as e:
            app.logger.error(f'Error processing PDF: {e}')
            return f"An error occurred: {str(e)}", 500

    return "Something went wrong", 500

@app.route('/', methods=['GET'])
def home():
    return "home works"

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Server Error: %s', error)
    return str(error), 500

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error('Unhandled Exception: %s', error)
    return str(error), 500

if __name__ == '__main__':
    app.run(debug=True)
