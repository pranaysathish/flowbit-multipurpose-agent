import re
import io
import PyPDF2
from typing import Dict, Any, List, Optional
import json

class PDFAgent:
    """
    PDF Agent that extracts fields from PDF documents and flags important information.
    Parses line-item invoice data or policy documents and flags specific conditions.
    """
    
    def __init__(self, memory_store):
        self.memory_store = memory_store
        
        # Define compliance keywords to flag
        self.compliance_keywords = [
            "GDPR", "FDA", "HIPAA", "PCI DSS", "SOX", "CCPA", "GLBA", 
            "FERPA", "COPPA", "FISMA", "ITAR", "EAR", "NERC CIP",
            "ISO 27001", "NIST", "compliance", "regulation", "regulatory",
            "data protection", "privacy policy", "personal data"
        ]
    
    def process(self, request_id: str, content: Any) -> Dict[str, Any]:
        """
        Process a PDF document to extract fields and flag important information
        
        Args:
            request_id: The unique identifier for the request
            content: The PDF content (bytes, string path, or PyPDF2 object)
            
        Returns:
            Dict containing extracted fields and analysis
        """
        # Parse PDF content
        pdf_text, pdf_metadata = self._parse_pdf(content)
        
        # Determine document type
        document_type = self._determine_document_type(pdf_text)
        
        # Extract fields based on document type
        if document_type == "INVOICE":
            extracted_fields = self._extract_invoice_fields(pdf_text)
            flags = self._flag_invoice_issues(extracted_fields)
        elif document_type == "POLICY":
            extracted_fields = self._extract_policy_fields(pdf_text)
            flags = self._flag_policy_issues(extracted_fields, pdf_text)
        else:
            extracted_fields = self._extract_general_fields(pdf_text)
            flags = self._flag_general_issues(extracted_fields, pdf_text)
        
        # Create result
        result = {
            "document_type": document_type,
            "metadata": pdf_metadata,
            "extracted_fields": extracted_fields,
            "flags": flags,
            "alert_needed": len(flags) > 0
        }
        
        # Store processing result in memory
        self.memory_store.store_processing_result(request_id, "pdf_agent", result)
        
        # Add detailed trace
        self.memory_store.add_trace(
            request_id,
            "pdf_agent",
            "pdf_processing_details",
            {
                "document_identification": {
                    "document_type": document_type,
                    "confidence": self._get_document_type_confidence(document_type, pdf_text)
                },
                "extraction_details": {
                    "field_count": len(extracted_fields),
                    "extraction_method": f"{document_type.lower()}_extraction"
                },
                "flag_details": {
                    "flag_count": len(flags),
                    "flag_types": list(set(f["type"] for f in flags)) if flags else []
                }
            }
        )
        
        return result
    
    def _parse_pdf(self, content: Any) -> tuple:
        """
        Parse PDF content into text and metadata
        
        Returns:
            Tuple of (pdf_text, pdf_metadata)
        """
        pdf_text = ""
        pdf_metadata = {}
        
        try:
            # Handle different input types
            if isinstance(content, bytes):
                pdf_file = PyPDF2.PdfReader(io.BytesIO(content))
            elif isinstance(content, dict) and "file_path" in content:
                # If it's a reference to a file path
                pdf_file = PyPDF2.PdfReader(content["file_path"])
            elif isinstance(content, str):
                # If it's a file path
                if content.lower().endswith('.pdf'):
                    pdf_file = PyPDF2.PdfReader(content)
                else:
                    # If it's PDF content as a string (unlikely but possible)
                    pdf_file = PyPDF2.PdfReader(io.BytesIO(content.encode('utf-8')))
            else:
                # Assume it's already a PyPDF2 object or similar
                pdf_file = content
            
            # Extract text from all pages
            for page_num in range(len(pdf_file.pages)):
                page = pdf_file.pages[page_num]
                pdf_text += page.extract_text() + "\n\n"
            
            # Extract metadata if available
            if hasattr(pdf_file, 'metadata') and pdf_file.metadata:
                for key, value in pdf_file.metadata.items():
                    if isinstance(key, str) and key.startswith('/'):
                        clean_key = key[1:]  # Remove leading slash
                        pdf_metadata[clean_key] = str(value)
        
        except Exception as e:
            # Handle parsing errors
            pdf_text = f"Error parsing PDF: {str(e)}"
            pdf_metadata = {"error": str(e)}
        
        return pdf_text, pdf_metadata
    
    def _determine_document_type(self, pdf_text: str) -> str:
        """Determine the type of PDF document based on its content"""
        
        pdf_text_lower = pdf_text.lower()
        
        # Check for invoice indicators
        invoice_indicators = [
            "invoice", "bill", "receipt", "payment", "amount due",
            "total due", "balance due", "invoice number", "invoice date",
            "bill to", "ship to", "payment terms", "subtotal", "tax"
        ]
        
        invoice_score = sum(1 for indicator in invoice_indicators if indicator in pdf_text_lower)
        
        # Check for policy document indicators
        policy_indicators = [
            "policy", "agreement", "terms and conditions", "privacy",
            "compliance", "regulation", "guidelines", "procedure",
            "protocol", "standard operating procedure", "sop",
            "effective date", "revision date", "version"
        ]
        
        policy_score = sum(1 for indicator in policy_indicators if indicator in pdf_text_lower)
        
        # Determine document type based on scores
        if invoice_score > policy_score and invoice_score >= 3:
            return "INVOICE"
        elif policy_score > invoice_score and policy_score >= 3:
            return "POLICY"
        else:
            return "GENERAL"
    
    def _extract_invoice_fields(self, pdf_text: str) -> Dict[str, Any]:
        """Extract fields from an invoice document"""
        
        extracted_fields = {}
        
        # Extract invoice number
        invoice_number_pattern = r'(?:invoice|bill|receipt)(?:\s+(?:no|num|number|#))?\s*[:#]?\s*([A-Z0-9][-A-Z0-9]*)'
        invoice_number_match = re.search(invoice_number_pattern, pdf_text, re.IGNORECASE)
        if invoice_number_match:
            extracted_fields["invoice_number"] = invoice_number_match.group(1).strip()
        
        # Extract invoice date
        date_pattern = r'(?:invoice|bill|receipt)(?:\s+date)?\s*[:#]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})'
        date_match = re.search(date_pattern, pdf_text, re.IGNORECASE)
        if date_match:
            extracted_fields["invoice_date"] = date_match.group(1).strip()
        
        # Extract total amount
        total_pattern = r'(?:total|amount\s+due|balance\s+due|grand\s+total)\s*[:#]?\s*[$€£]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        total_match = re.search(total_pattern, pdf_text, re.IGNORECASE)
        if total_match:
            total_str = total_match.group(1).strip()
            # Remove commas for numeric conversion
            total_str = total_str.replace(',', '')
            try:
                extracted_fields["total_amount"] = float(total_str)
            except ValueError:
                extracted_fields["total_amount_raw"] = total_str
        
        # Extract currency
        currency_pattern = r'(?:total|amount\s+due|balance\s+due|grand\s+total)\s*[:#]?\s*([$€£])\s*\d'
        currency_match = re.search(currency_pattern, pdf_text, re.IGNORECASE)
        if currency_match:
            currency_symbol = currency_match.group(1).strip()
            currency_map = {'$': 'USD', '€': 'EUR', '£': 'GBP'}
            extracted_fields["currency"] = currency_map.get(currency_symbol, currency_symbol)
        
        # Extract line items
        # This is a simplified approach - real implementation would be more sophisticated
        line_items = []
        
        # Look for sections that might contain line items
        lines = pdf_text.split('\n')
        in_items_section = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line might be a header for line items
            if re.search(r'item|description|product|service|qty|quantity|price|amount', line, re.IGNORECASE):
                in_items_section = True
                continue
            
            # Check if this line might be a footer (end of line items)
            if in_items_section and re.search(r'subtotal|total|tax', line, re.IGNORECASE):
                in_items_section = False
                continue
            
            # If we're in the items section, try to parse a line item
            if in_items_section:
                # Look for patterns like: description followed by quantity and price
                item_match = re.search(r'(.+?)\s+(\d+)\s+[$€£]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', line)
                if item_match:
                    description = item_match.group(1).strip()
                    quantity = int(item_match.group(2))
                    price_str = item_match.group(3).replace(',', '')
                    
                    try:
                        price = float(price_str)
                        line_items.append({
                            "description": description,
                            "quantity": quantity,
                            "price": price
                        })
                    except ValueError:
                        pass
        
        if line_items:
            extracted_fields["line_items"] = line_items
        
        return extracted_fields
    
    def _extract_policy_fields(self, pdf_text: str) -> Dict[str, Any]:
        """Extract fields from a policy document"""
        
        extracted_fields = {}
        
        # Extract policy number
        policy_number_pattern = r'(?:policy|document)(?:\s+(?:no|num|number|#))?\s*[:#]?\s*([A-Z0-9][-A-Z0-9]*)'
        policy_number_match = re.search(policy_number_pattern, pdf_text, re.IGNORECASE)
        if policy_number_match:
            extracted_fields["policy_number"] = policy_number_match.group(1).strip()
        
        # Extract effective date
        effective_date_pattern = r'(?:effective|valid from|start)(?:\s+date)?\s*[:#]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})'
        effective_date_match = re.search(effective_date_pattern, pdf_text, re.IGNORECASE)
        if effective_date_match:
            extracted_fields["effective_date"] = effective_date_match.group(1).strip()
        
        # Extract version or revision
        version_pattern = r'(?:version|revision|rev)\.?\s*[:#]?\s*([\d\.]+)'
        version_match = re.search(version_pattern, pdf_text, re.IGNORECASE)
        if version_match:
            extracted_fields["version"] = version_match.group(1).strip()
        
        # Extract compliance references
        compliance_references = []
        for keyword in self.compliance_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', pdf_text, re.IGNORECASE):
                compliance_references.append(keyword)
        
        if compliance_references:
            extracted_fields["compliance_references"] = compliance_references
        
        # Extract sections (simplified approach)
        sections = {}
        current_section = None
        section_content = []
        
        lines = pdf_text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line might be a section header
            if re.match(r'^[1-9IVX]+\.?\s+[A-Z]', line) or re.match(r'^[A-Z][A-Z\s]{2,}', line):
                # Save previous section if exists
                if current_section and section_content:
                    sections[current_section] = ' '.join(section_content)
                
                current_section = line
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # Save the last section
        if current_section and section_content:
            sections[current_section] = ' '.join(section_content)
        
        if sections:
            extracted_fields["sections"] = sections
        
        return extracted_fields
    
    def _extract_general_fields(self, pdf_text: str) -> Dict[str, Any]:
        """Extract general fields from a document"""
        
        extracted_fields = {}
        
        # Extract document title (first non-empty line or line with largest font)
        lines = pdf_text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                extracted_fields["title"] = line
                break
        
        # Extract dates
        date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b'
        dates = re.findall(date_pattern, pdf_text, re.IGNORECASE)
        if dates:
            extracted_fields["dates"] = dates
        
        # Extract monetary amounts
        amount_pattern = r'[$€£]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, pdf_text)
        if amounts:
            # Convert to float
            numeric_amounts = []
            for amount in amounts:
                try:
                    numeric_amounts.append(float(amount.replace(',', '')))
                except ValueError:
                    pass
            
            if numeric_amounts:
                extracted_fields["monetary_amounts"] = numeric_amounts
        
        # Extract compliance references
        compliance_references = []
        for keyword in self.compliance_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', pdf_text, re.IGNORECASE):
                compliance_references.append(keyword)
        
        if compliance_references:
            extracted_fields["compliance_references"] = compliance_references
        
        return extracted_fields
    
    def _flag_invoice_issues(self, extracted_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flag issues in invoice documents"""
        
        flags = []
        
        # Flag high-value invoices (>10,000)
        if "total_amount" in extracted_fields:
            total_amount = extracted_fields["total_amount"]
            if total_amount > 10000:
                flags.append({
                    "type": "high_value_invoice",
                    "description": f"Invoice total amount ({total_amount}) exceeds 10,000",
                    "severity": "HIGH"
                })
        
        # Flag missing critical fields
        critical_fields = ["invoice_number", "invoice_date", "total_amount"]
        missing_fields = [field for field in critical_fields if field not in extracted_fields]
        
        if missing_fields:
            flags.append({
                "type": "missing_critical_fields",
                "description": f"Missing critical fields: {', '.join(missing_fields)}",
                "severity": "MEDIUM"
            })
        
        # Flag suspicious line items (if any)
        if "line_items" in extracted_fields:
            line_items = extracted_fields["line_items"]
            
            # Check for unusually expensive items
            expensive_items = []
            for item in line_items:
                if "price" in item and item["price"] > 5000:
                    expensive_items.append(item["description"])
            
            if expensive_items:
                flags.append({
                    "type": "expensive_line_items",
                    "description": f"Unusually expensive line items: {', '.join(expensive_items)}",
                    "severity": "MEDIUM"
                })
        
        return flags
    
    def _flag_policy_issues(self, extracted_fields: Dict[str, Any], pdf_text: str) -> List[Dict[str, Any]]:
        """Flag issues in policy documents"""
        
        flags = []
        
        # Flag compliance references
        if "compliance_references" in extracted_fields:
            compliance_refs = extracted_fields["compliance_references"]
            if compliance_refs:
                flags.append({
                    "type": "compliance_references",
                    "description": f"Document references compliance standards: {', '.join(compliance_refs)}",
                    "severity": "MEDIUM"
                })
        
        # Flag specific compliance keywords
        high_priority_compliance = ["GDPR", "FDA", "HIPAA", "PCI DSS"]
        referenced_high_priority = []
        
        for keyword in high_priority_compliance:
            if re.search(r'\b' + re.escape(keyword) + r'\b', pdf_text, re.IGNORECASE):
                referenced_high_priority.append(keyword)
        
        if referenced_high_priority:
            flags.append({
                "type": "high_priority_compliance",
                "description": f"Document references high-priority compliance: {', '.join(referenced_high_priority)}",
                "severity": "HIGH"
            })
        
        # Flag missing version or effective date
        critical_fields = ["policy_number", "effective_date", "version"]
        missing_fields = [field for field in critical_fields if field not in extracted_fields]
        
        if missing_fields:
            flags.append({
                "type": "missing_policy_metadata",
                "description": f"Missing policy metadata: {', '.join(missing_fields)}",
                "severity": "LOW"
            })
        
        return flags
    
    def _flag_general_issues(self, extracted_fields: Dict[str, Any], pdf_text: str) -> List[Dict[str, Any]]:
        """Flag issues in general documents"""
        
        flags = []
        
        # Flag compliance references
        if "compliance_references" in extracted_fields:
            compliance_refs = extracted_fields["compliance_references"]
            if compliance_refs:
                flags.append({
                    "type": "compliance_references",
                    "description": f"Document references compliance standards: {', '.join(compliance_refs)}",
                    "severity": "MEDIUM"
                })
        
        # Flag high monetary amounts
        if "monetary_amounts" in extracted_fields:
            amounts = extracted_fields["monetary_amounts"]
            high_amounts = [amount for amount in amounts if amount > 10000]
            
            if high_amounts:
                flags.append({
                    "type": "high_monetary_amounts",
                    "description": f"Document contains high monetary amounts: {', '.join([str(amount) for amount in high_amounts])}",
                    "severity": "MEDIUM"
                })
        
        # Flag potentially sensitive information
        sensitive_patterns = [
            (r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', "SSN_PATTERN"),
            (r'\b\d{16}\b', "CREDIT_CARD_PATTERN"),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "EMAIL_PATTERN")
        ]
        
        found_sensitive = []
        for pattern, pattern_name in sensitive_patterns:
            if re.search(pattern, pdf_text):
                found_sensitive.append(pattern_name)
        
        if found_sensitive:
            flags.append({
                "type": "potential_sensitive_info",
                "description": f"Document may contain sensitive information patterns: {', '.join(found_sensitive)}",
                "severity": "HIGH"
            })
        
        return flags
    
    def _get_document_type_confidence(self, document_type: str, pdf_text: str) -> float:
        """Get confidence score for document type classification"""
        
        pdf_text_lower = pdf_text.lower()
        
        # Define indicators for each document type
        indicators = {
            "INVOICE": [
                "invoice", "bill", "receipt", "payment", "amount due",
                "total due", "balance due", "invoice number", "invoice date",
                "bill to", "ship to", "payment terms", "subtotal", "tax"
            ],
            "POLICY": [
                "policy", "agreement", "terms and conditions", "privacy",
                "compliance", "regulation", "guidelines", "procedure",
                "protocol", "standard operating procedure", "sop",
                "effective date", "revision date", "version"
            ],
            "GENERAL": []  # No specific indicators for general type
        }
        
        # Count indicators for the determined type
        if document_type in indicators:
            type_indicators = indicators[document_type]
            indicator_count = sum(1 for indicator in type_indicators if indicator in pdf_text_lower)
            
            # Calculate confidence based on indicator count
            if document_type == "GENERAL":
                return 0.5  # Default confidence for general type
            elif len(type_indicators) > 0:
                confidence = min(0.95, 0.5 + (indicator_count / len(type_indicators) * 0.5))
                return round(confidence, 2)
        
        return 0.5  # Default confidence
