import os
import shutil
import json
import PyPDF2
from fastapi import UploadFile
from typing import Any, Dict, Optional
import io

def save_upload_file(upload_file: UploadFile, destination_folder: str) -> str:
    """
    Save an uploaded file to the specified destination folder
    
    Args:
        upload_file: The uploaded file
        destination_folder: The folder to save the file to
        
    Returns:
        The path to the saved file
    """
    # Create destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)
    
    # Generate file path
    file_path = os.path.join(destination_folder, upload_file.filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    # Reset file pointer
    upload_file.file.seek(0)
    
    return file_path

def get_file_extension(filename: str) -> str:
    """
    Get the extension of a file
    
    Args:
        filename: The name of the file
        
    Returns:
        The extension of the file (lowercase, without the dot)
    """
    if not filename or "." not in filename:
        return ""
    
    return filename.split(".")[-1].lower()

def get_file_content(file_path: str, file_extension: str) -> Any:
    """
    Get the content of a file based on its extension
    
    Args:
        file_path: The path to the file
        file_extension: The extension of the file
        
    Returns:
        The content of the file in an appropriate format
    """
    if file_extension == "json":
        # Parse JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    elif file_extension == "pdf":
        # Return PDF content as bytes for processing by PDF agent
        with open(file_path, "rb") as f:
            return f.read()
    
    elif file_extension in ["txt", "html", "csv", "md"]:
        # Return text content
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    elif file_extension in ["eml", "msg"]:
        # Return email content as string
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    else:
        # For unsupported file types, return binary content
        with open(file_path, "rb") as f:
            return f.read()

def create_sample_file(file_type: str, output_path: str) -> str:
    """
    Create a sample file for testing
    
    Args:
        file_type: The type of file to create (email, json, pdf)
        output_path: The path to save the file to
        
    Returns:
        The path to the created file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if file_type == "email":
        # Create a sample email file
        email_content = """From: customer@example.com
To: support@flowbit.ai
Subject: Urgent: Issue with recent order #12345

Hello,

I'm having a serious issue with my recent order #12345 placed on May 25, 2025.
The product arrived damaged and I need an immediate replacement.
This is the third time I've had issues with your service and I'm very disappointed.

Please escalate this to your manager as I need this resolved ASAP.

Regards,
John Smith
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(email_content)
    
    elif file_type == "json":
        # Create a sample JSON webhook file
        json_content = {
            "event_type": "order_created",
            "timestamp": "2025-05-30T12:34:56Z",
            "data": {
                "order_id": "ORD-12345",
                "customer_id": "CUST-6789",
                "items": [
                    {
                        "product_id": "PROD-001",
                        "name": "Premium Widget",
                        "quantity": 2,
                        "price": 99.99
                    },
                    {
                        "product_id": "PROD-002",
                        "name": "Deluxe Gadget",
                        "quantity": 1,
                        "price": 149.99
                    }
                ],
                "total": 349.97,
                "currency": "USD",
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345",
                    "country": "USA"
                }
            }
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)
    
    elif file_type == "pdf":
        # Create a simple PDF file using PyPDF2
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create a temporary PDF using reportlab
            temp_path = output_path + ".temp"
            c = canvas.Canvas(temp_path, pagesize=letter)
            
            # Add invoice-like content
            c.setFont("Helvetica-Bold", 18)
            c.drawString(72, 750, "INVOICE")
            
            c.setFont("Helvetica", 12)
            c.drawString(72, 720, "Invoice #: INV-12345")
            c.drawString(72, 700, "Date: May 30, 2025")
            c.drawString(72, 680, "Due Date: June 15, 2025")
            
            c.drawString(72, 650, "Bill To:")
            c.drawString(72, 630, "Acme Corporation")
            c.drawString(72, 610, "123 Business Ave")
            c.drawString(72, 590, "Corporate City, BZ 54321")
            
            c.drawString(72, 540, "Description")
            c.drawString(300, 540, "Quantity")
            c.drawString(400, 540, "Price")
            c.drawString(500, 540, "Amount")
            
            c.line(72, 535, 550, 535)
            
            c.drawString(72, 510, "Enterprise Software License")
            c.drawString(300, 510, "1")
            c.drawString(400, 510, "$15,000.00")
            c.drawString(500, 510, "$15,000.00")
            
            c.drawString(72, 490, "Support & Maintenance (1 year)")
            c.drawString(300, 490, "1")
            c.drawString(400, 490, "$3,000.00")
            c.drawString(500, 490, "$3,000.00")
            
            c.line(72, 450, 550, 450)
            
            c.drawString(400, 430, "Subtotal:")
            c.drawString(500, 430, "$18,000.00")
            c.drawString(400, 410, "Tax (8%):")
            c.drawString(500, 410, "$1,440.00")
            c.drawString(400, 390, "Total:")
            c.drawString(500, 390, "$19,440.00")
            
            c.drawString(72, 330, "This invoice contains references to GDPR compliance requirements.")
            
            c.save()
            
            # Use PyPDF2 to finalize the PDF
            reader = PyPDF2.PdfReader(temp_path)
            writer = PyPDF2.PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            with open(output_path, "wb") as f:
                writer.write(f)
            
            # Remove temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except ImportError:
            # If reportlab is not available, create a simple PDF with PyPDF2 only
            writer = PyPDF2.PdfWriter()
            page = PyPDF2.PageObject.create_blank_page(width=612, height=792)
            writer.add_page(page)
            
            with open(output_path, "wb") as f:
                writer.write(f)
    
    return output_path
