from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_invoice_pdf(output_path):
    """Create a sample invoice PDF file for testing"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Add invoice content
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 750, "INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "Invoice #: INV-56789")
    c.drawString(72, 700, "Date: May 30, 2025")
    c.drawString(72, 680, "Due Date: June 15, 2025")
    
    c.drawString(72, 650, "Bill To:")
    c.drawString(72, 630, "TechCorp International")
    c.drawString(72, 610, "789 Technology Park")
    c.drawString(72, 590, "Silicon Valley, CA 94025")
    
    c.drawString(72, 540, "Description")
    c.drawString(300, 540, "Quantity")
    c.drawString(400, 540, "Price")
    c.drawString(500, 540, "Amount")
    
    c.line(72, 535, 550, 535)
    
    c.drawString(72, 510, "Enterprise AI Platform License")
    c.drawString(300, 510, "1")
    c.drawString(400, 510, "$25,000.00")
    c.drawString(500, 510, "$25,000.00")
    
    c.drawString(72, 490, "Implementation Services")
    c.drawString(300, 490, "1")
    c.drawString(400, 490, "$10,000.00")
    c.drawString(500, 490, "$10,000.00")
    
    c.drawString(72, 470, "Premium Support (1 year)")
    c.drawString(300, 470, "1")
    c.drawString(400, 470, "$5,000.00")
    c.drawString(500, 470, "$5,000.00")
    
    c.line(72, 450, 550, 450)
    
    c.drawString(400, 430, "Subtotal:")
    c.drawString(500, 430, "$40,000.00")
    c.drawString(400, 410, "Tax (8.5%):")
    c.drawString(500, 410, "$3,400.00")
    c.drawString(400, 390, "Total:")
    c.drawString(500, 390, "$43,400.00")
    
    c.drawString(72, 330, "Payment Terms: Net 30")
    c.drawString(72, 310, "Please make checks payable to: FlowbitAI Technologies, Inc.")
    
    c.drawString(72, 270, "Thank you for your business!")
    
    c.save()
    
    return output_path

def create_policy_pdf(output_path):
    """Create a sample policy document PDF for testing"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Add policy content
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 750, "DATA PROCESSING POLICY")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "Policy #: POL-12345")
    c.drawString(72, 700, "Effective Date: June 1, 2025")
    c.drawString(72, 680, "Version: 2.1")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 640, "1. Introduction")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 620, "This policy outlines the procedures for handling customer data in compliance")
    c.drawString(72, 600, "with GDPR, CCPA, and other applicable regulations.")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 560, "2. Scope")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 540, "This policy applies to all employees, contractors, and third-party vendors")
    c.drawString(72, 520, "who process customer data on behalf of the company.")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 480, "3. GDPR Compliance")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 460, "All data processing activities must comply with the General Data Protection")
    c.drawString(72, 440, "Regulation (GDPR) requirements, including but not limited to:")
    c.drawString(72, 420, "- Lawful basis for processing")
    c.drawString(72, 400, "- Data minimization")
    c.drawString(72, 380, "- Purpose limitation")
    c.drawString(72, 360, "- Storage limitation")
    c.drawString(72, 340, "- Integrity and confidentiality")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 300, "4. FDA Regulated Data")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 280, "When processing data related to FDA regulated products, additional")
    c.drawString(72, 260, "safeguards must be implemented to ensure compliance with FDA regulations.")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 220, "5. Enforcement")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 200, "Violations of this policy may result in disciplinary action, up to and")
    c.drawString(72, 180, "including termination of employment or contract.")
    
    c.save()
    
    return output_path

if __name__ == "__main__":
    create_invoice_pdf("samples/pdf/high_value_invoice.pdf")
    create_policy_pdf("samples/pdf/compliance_policy.pdf")
    print("Sample PDF files created successfully.")
