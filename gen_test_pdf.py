from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_test_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title (Large Font)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "A Novel Approach to AI Research")
    
    # Authors
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, "John Doe, Jane Smith")
    
    # Abstract
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 160, "Abstract")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 180, "This is the abstract text. It summarizes the paper.")
    
    # Introduction
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 220, "Introduction")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 240, "This is the introduction. It introduces the topic.")
    
    # Methodology
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 280, "Methodology")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 300, "We used a complex algorithm.")
    
    c.save()

if __name__ == "__main__":
    create_test_pdf("test_paper.pdf")
    print("Created test_paper.pdf")
