import json
import re
from typing import Dict, Any, List, Optional
import os
from pathlib import Path
import PyPDF2
import email
from email import policy
from email.parser import BytesParser

class ClassifierAgent:
    """
    Classifier Agent that detects both format and business intent of the input.
    Uses pattern matching and few-shot examples for classification.
    """
    
    def __init__(self, memory_store):
        self.memory_store = memory_store
        self.format_types = ["EMAIL", "JSON", "PDF", "MIXED"]
        self.intent_types = ["RFQ", "COMPLAINT", "INVOICE", "REGULATION", "FRAUD_RISK", "GENERAL"]
        
        # Few-shot examples for intent classification
        self.intent_examples = {
            "RFQ": [
                "request for quote",
                "price inquiry",
                "cost estimate",
                "quotation needed",
                "pricing information",
                "product availability",
                "service quote",
                "quote request",
                "pricing quote",
                "estimate request"
            ],
            "COMPLAINT": [
                "not satisfied",
                "poor service",
                "complaint",
                "issue with",
                "problem with",
                "dissatisfied",
                "doesn't work",
                "failed to",
                "refund",
                "disappointed",
                "unhappy",
                "terrible experience",
                "bad quality",
                "not working",
                "damaged"
            ],
            "INVOICE": [
                "invoice",
                "payment due",
                "bill",
                "receipt",
                "amount due",
                "payment terms",
                "paid in full",
                "tax invoice",
                "billing details",
                "invoice number",
                "invoice date",
                "due date",
                "subtotal",
                "total",
                "bill to",
                "ship to",
                "purchase order",
                "quantity",
                "unit price",
                "description",
                "item",
                "payment method",
                "tax",
                "amount",
                "balance",
                "pay"
            ],
            "REGULATION": [
                "compliance",
                "regulation",
                "legal requirement",
                "GDPR",
                "FDA",
                "policy",
                "regulatory",
                "compliance requirement",
                "law",
                "directive",
                "privacy policy",
                "terms of service",
                "data protection",
                "legal",
                "compliance report"
            ],
            "FRAUD_RISK": [
                "suspicious",
                "fraud",
                "unusual activity",
                "security breach",
                "unauthorized",
                "identity theft",
                "scam",
                "phishing",
                "money laundering",
                "risk alert",
                "suspicious transaction",
                "unusual pattern",
                "security alert",
                "compromised",
                "fraudulent",
                "risk",
                "alert",
                "transaction_risk",
                "risk_level",
                "high risk",
                "medium risk",
                "block",
                "flag",
                "review",
                "unusual_location",
                "velocity",
                "threshold",
                "exceeded",
                "multiple attempts",
                "risk_factors",
                "confidence_score",
                "recommended_action"
            ]
        }
    
    def classify(self, request_id: str, content: Any, input_source: str) -> Dict[str, Any]:
        """
        Classify the input format and business intent
        
        Args:
            request_id: The unique identifier for the request
            content: The content to classify
            input_source: The source of the input (file, json, email)
            
        Returns:
            Dict containing format, intent, confidence, and priority
        """
        # Detect format
        format_type = self._detect_format(content, input_source)
        
        # Detect intent
        intent_type, confidence = self._detect_intent(content, format_type)
        
        # Determine priority based on intent and content
        priority = self._determine_priority(intent_type, content, format_type)
        
        # Create classification result
        classification = {
            "format": format_type,
            "intent": intent_type,
            "confidence": confidence,
            "priority": priority
        }
        
        # Store classification in memory
        self.memory_store.store_classification(request_id, classification)
        
        # Add detailed trace with classification reasoning
        self.memory_store.add_trace(
            request_id,
            "classifier_agent",
            "classification_details",
            {
                "format_detection": {
                    "detected_format": format_type,
                    "input_source": input_source
                },
                "intent_detection": {
                    "detected_intent": intent_type,
                    "confidence": confidence,
                    "matched_keywords": self._get_matched_keywords(content, intent_type, format_type)
                },
                "priority_determination": {
                    "assigned_priority": priority,
                    "reasoning": self._get_priority_reasoning(intent_type, content, format_type)
                }
            }
        )
        
        return classification
    
    def _detect_format(self, content: Any, input_source: str) -> str:
        """Detect the format of the input content"""
        
        # If source is explicitly specified, use that as a hint
        if input_source == "file":
            if isinstance(content, dict) and "file_path" in content:
                file_path = content["file_path"]
                if file_path.lower().endswith(".pdf"):
                    return "PDF"
                elif file_path.lower().endswith(".json"):
                    return "JSON"
                elif file_path.lower().endswith(".eml") or file_path.lower().endswith(".txt"):
                    return "EMAIL"
        elif input_source == "json":
            return "JSON"
        elif input_source == "email":
            return "EMAIL"
        
        # Otherwise, try to detect based on content
        if isinstance(content, dict) or isinstance(content, list):
            return "JSON"
        elif isinstance(content, str):
            # Check if it's a JSON string
            try:
                json.loads(content)
                return "JSON"
            except:
                pass
            
            # Check if it looks like an email (more comprehensive check)
            email_indicators = [
                "From:", "To:", "Subject:", "Date:", "Cc:", "Bcc:", "Reply-To:",
                "SECURITY ALERT", "URGENT", "Dear", "Hello", "Hi,", "Sincerely,", "Regards,",
                "@" # Email addresses often contain @
            ]
            
            # Count how many email indicators are present
            indicator_count = sum(1 for indicator in email_indicators if indicator in content)
            
            # If multiple indicators are present, it's likely an email
            if indicator_count >= 2:
                return "EMAIL"
            
            # Check for common email structural patterns
            if re.search(r'[\w\.-]+@[\w\.-]+', content):  # Contains email address
                return "EMAIL"
        
        # Default to PDF for binary content
        if isinstance(content, bytes):
            return "PDF"
        
        # Default to MIXED if format can't be determined
        return "MIXED"
    
    def _detect_intent(self, content: Any, format_type: str) -> tuple:
        """
        Detect the business intent of the content
        
        Returns:
            Tuple of (intent_type, confidence)
        """
        # Special handling for JSON data with explicit type indicators
        if format_type == "JSON" and isinstance(content, dict):
            # Check for explicit type indicators in JSON
            alert_type = None
            if "alert_type" in content:
                alert_type = str(content["alert_type"]).lower()
            elif "type" in content:
                alert_type = str(content["type"]).lower()
            elif "document_type" in content:
                alert_type = str(content["document_type"]).lower()
            
            # Map alert types to intents
            if alert_type:
                if any(risk_term in alert_type for risk_term in ["risk", "fraud", "security", "alert", "suspicious"]):
                    return "FRAUD_RISK", 1.0
                elif any(invoice_term in alert_type for invoice_term in ["invoice", "bill", "payment", "receipt"]):
                    return "INVOICE", 1.0
                elif any(complaint_term in alert_type for complaint_term in ["complaint", "issue", "problem", "ticket"]):
                    return "COMPLAINT", 1.0
                elif any(rfq_term in alert_type for rfq_term in ["quote", "rfq", "inquiry", "pricing"]):
                    return "RFQ", 1.0
                elif any(reg_term in alert_type for reg_term in ["regulation", "compliance", "policy", "legal"]):
                    return "REGULATION", 1.0
            
            # Check for risk factors
            if "risk_factors" in content and isinstance(content["risk_factors"], list) and len(content["risk_factors"]) > 0:
                return "FRAUD_RISK", 1.0
        
        # Convert content to text for analysis based on format
        text = self._extract_text_for_analysis(content, format_type)
        
        # Count keyword matches for each intent
        intent_scores = {}
        for intent, keywords in self.intent_examples.items():
            score = 0
            for keyword in keywords:
                # Case-insensitive search
                matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE))
                score += matches
            
            intent_scores[intent] = score
        
        # Find the intent with the highest score
        if not intent_scores or max(intent_scores.values()) == 0:
            return "GENERAL", 0.5
        
        max_score = max(intent_scores.values())
        max_intent = max(intent_scores, key=intent_scores.get)
        
        # Calculate confidence (normalize score)
        total_score = sum(intent_scores.values())
        confidence = intent_scores[max_intent] / total_score if total_score > 0 else 0.5
        
        return max_intent, round(confidence, 2)
    
    def _extract_text_for_analysis(self, content: Any, format_type: str) -> str:
        """Extract text from content based on its format for intent analysis"""
        
        # Handle JSON format
        if format_type == "JSON":
            if isinstance(content, dict) or isinstance(content, list):
                # For JSON objects, do a deep extraction of values and keys for better analysis
                extracted_text = self._extract_json_values(content)
                return extracted_text
            elif isinstance(content, str):
                try:
                    # Try to parse JSON string and extract values
                    json_obj = json.loads(content)
                    return self._extract_json_values(json_obj)
                except:
                    return content
            return str(content)
        
        # Handle Email format
        elif format_type == "EMAIL":
            if isinstance(content, str):
                # Extract subject and body from email text
                subject_match = re.search(r'Subject: (.*?)(\n|$)', content)
                subject = subject_match.group(1) if subject_match else ""
                
                # Simple extraction of body (after headers)
                body = ""
                in_body = False
                for line in content.split('\n'):
                    if in_body:
                        body += line + " "
                    elif line.strip() == "":
                        in_body = True
                
                # If we couldn't extract the body properly, just use the whole content
                if not body.strip():
                    return content
                
                return subject + " " + body
            return str(content)
        
        # Handle PDF format
        elif format_type == "PDF":
            # Handle PDF content more effectively
            if isinstance(content, dict) and "file_path" in content:
                # If we have a file path reference, try to extract text from the PDF
                try:
                    import PyPDF2
                    pdf_file = PyPDF2.PdfReader(content["file_path"])
                    pdf_text = ""
                    for page_num in range(len(pdf_file.pages)):
                        page = pdf_file.pages[page_num]
                        pdf_text += page.extract_text() + "\n"
                    return pdf_text
                except Exception as e:
                    print(f"Error extracting text from PDF: {str(e)}")
                    return "PDF content for analysis"
            elif isinstance(content, bytes):
                # If we have binary content, try to extract text from it
                try:
                    import PyPDF2
                    import io
                    pdf_file = PyPDF2.PdfReader(io.BytesIO(content))
                    pdf_text = ""
                    for page_num in range(len(pdf_file.pages)):
                        page = pdf_file.pages[page_num]
                        pdf_text += page.extract_text() + "\n"
                    return pdf_text
                except Exception as e:
                    print(f"Error extracting text from PDF bytes: {str(e)}")
                    return "PDF content for analysis"
            elif isinstance(content, str) and content.lower().endswith('.pdf'):
                # If it's a file path string
                try:
                    import PyPDF2
                    pdf_file = PyPDF2.PdfReader(content)
                    pdf_text = ""
                    for page_num in range(len(pdf_file.pages)):
                        page = pdf_file.pages[page_num]
                        pdf_text += page.extract_text() + "\n"
                    return pdf_text
                except Exception as e:
                    print(f"Error extracting text from PDF path: {str(e)}")
                    return "PDF content for analysis"
            return str(content)
        
        # Default: return string representation
        return str(content)
    
    def _extract_json_values(self, json_obj: Any, prefix="") -> str:
        """Recursively extract values from JSON object for better text analysis"""
        result = []
        
        if isinstance(json_obj, dict):
            # Add all keys as they often contain important classification information
            result.extend(list(json_obj.keys()))
            
            # Process each key-value pair
            for key, value in json_obj.items():
                # Add key-value pairs for primitive types
                if isinstance(value, (str, int, float, bool)):
                    result.append(f"{key}: {value}")
                
                # Recursively process nested objects
                if isinstance(value, (dict, list)):
                    result.append(self._extract_json_values(value, prefix=f"{prefix}{key}."))
        
        elif isinstance(json_obj, list):
            # Process each item in the list
            for item in json_obj:
                if isinstance(item, (str, int, float, bool)):
                    result.append(str(item))
                elif isinstance(item, (dict, list)):
                    result.append(self._extract_json_values(item, prefix=prefix))
        
        return " ".join([str(item) for item in result])
    
    def _determine_priority(self, intent_type: str, content: Any, format_type: str) -> str:
        """Determine priority level based on intent and content"""
        
        # Default priority mapping based on intent
        intent_priority_map = {
            "FRAUD_RISK": "HIGH",
            "COMPLAINT": "MEDIUM",
            "REGULATION": "MEDIUM",
            "INVOICE": "LOW",
            "RFQ": "LOW",
            "GENERAL": "LOW"
        }
        
        # Start with default priority based on intent
        priority = intent_priority_map.get(intent_type, "LOW")
        
        # For JSON data, check for explicit priority indicators
        if format_type == "JSON" and isinstance(content, dict):
            # Check for explicit risk level or priority indicators
            risk_level = None
            
            # Direct risk level field
            if "risk_level" in content:
                risk_level = str(content["risk_level"]).lower()
            elif "priority" in content:
                risk_level = str(content["priority"]).lower()
            elif "severity" in content:
                risk_level = str(content["severity"]).lower()
            # Check nested fields
            elif "details" in content and isinstance(content["details"], dict):
                details = content["details"]
                if "risk_level" in details:
                    risk_level = str(details["risk_level"]).lower()
                elif "priority" in details:
                    risk_level = str(details["priority"]).lower()
                elif "severity" in details:
                    risk_level = str(details["severity"]).lower()
            
            # Set priority based on risk level
            if risk_level:
                if risk_level in ["high", "critical", "severe"]:
                    priority = "HIGH"
                elif risk_level in ["medium", "moderate"]:
                    priority = "MEDIUM"
                elif risk_level in ["low", "minor"]:
                    priority = "LOW"
            
            # Check for amount thresholds in financial transactions
            amount = None
            if "amount" in content and isinstance(content["amount"], (int, float)):
                amount = float(content["amount"])
            elif "details" in content and isinstance(content["details"], dict):
                details = content["details"]
                if "amount" in details and isinstance(details["amount"], (int, float)):
                    amount = float(details["amount"])
            
            # Set high priority for large amounts
            if amount and amount > 10000:
                priority = "HIGH"
            
            # Check for explicit recommended actions
            action = None
            if "recommended_action" in content:
                action = str(content["recommended_action"]).lower()
            elif "action" in content:
                action = str(content["action"]).lower()
            
            # Set priority based on recommended action
            if action and action in ["block", "reject", "escalate"]:
                priority = "HIGH"
        
        # Upgrade priority based on content analysis
        text = self._extract_text_for_analysis(content, format_type)
        
        # Check for urgent indicators
        urgent_keywords = ["urgent", "immediately", "asap", "emergency", "critical"]
        if any(keyword in text.lower() for keyword in urgent_keywords):
            if priority == "LOW":
                priority = "MEDIUM"
            elif priority == "MEDIUM":
                priority = "HIGH"
        
        # Check for fraud/security indicators
        fraud_keywords = ["fraud", "unauthorized", "suspicious", "breach", "stolen"]
        if any(keyword in text.lower() for keyword in fraud_keywords):
            priority = "HIGH"
        
        # For PDF documents, check if it's an invoice even if classified as GENERAL
        if format_type == "PDF" and intent_type == "GENERAL":
            invoice_indicators = ["invoice", "bill", "receipt", "amount due", "payment", "total", "subtotal", "tax"]
            invoice_score = sum(1 for indicator in invoice_indicators if indicator.lower() in text.lower())
            if invoice_score >= 3:
                # It's likely an invoice despite being classified as GENERAL
                intent_type = "INVOICE"
        
        # Check for high-value indicators in invoices or invoice-like documents
        if intent_type == "INVOICE" or (format_type == "PDF" and "invoice" in text.lower()):
            # Look for currency amounts with various patterns
            currency_patterns = [
                r'[$€£]\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $10,000.00
                r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*[$€£]',  # 10,000.00$
                r'total\s*:?\s*[$€£]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Total: $10,000.00
                r'amount\s*:?\s*[$€£]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Amount: $10,000.00
                r'balance\s*:?\s*[$€£]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Balance: $10,000.00
                r'due\s*:?\s*[$€£]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'  # Due: $10,000.00
            ]
            
            # Find all amounts in the text
            amounts = []
            for pattern in currency_patterns:
                amounts.extend(re.findall(pattern, text, re.IGNORECASE))
            
            # Extract numeric values
            numeric_values = []
            for amount in amounts:
                # Remove non-numeric characters except decimal point
                cleaned = re.sub(r'[^0-9.]', '', amount)
                try:
                    # Handle cases where we might have multiple decimal points after cleanup
                    if cleaned.count('.') > 1:
                        parts = cleaned.split('.')
                        cleaned = parts[0] + '.' + parts[1]
                    numeric_values.append(float(cleaned))
                except ValueError:
                    pass
            
            # If any amount is greater than 10,000, upgrade priority
            if numeric_values and max(numeric_values) > 10000:
                priority = "HIGH"
                print(f"High-value invoice detected: {max(numeric_values)}")
        
        return priority
    
    def _get_matched_keywords(self, content: Any, intent_type: str, format_type: str) -> List[str]:
        """Get the keywords that matched for the detected intent"""
        text = self._extract_text_for_analysis(content, format_type)
        matched_keywords = []
        
        if intent_type in self.intent_examples:
            for keyword in self.intent_examples[intent_type]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                    matched_keywords.append(keyword)
        
        return matched_keywords
    
    def _get_priority_reasoning(self, intent_type: str, content: Any, format_type: str) -> str:
        """Get reasoning for the assigned priority"""
        text = self._extract_text_for_analysis(content, format_type)
        
        # Check for urgent indicators
        urgent_keywords = ["urgent", "immediately", "asap", "emergency", "critical"]
        urgent_matches = [k for k in urgent_keywords if k in text.lower()]
        
        # Check for fraud/security indicators
        fraud_keywords = ["fraud", "unauthorized", "suspicious", "breach", "stolen"]
        fraud_matches = [k for k in fraud_keywords if k in text.lower()]
        
        # Build reasoning
        reasoning = []
        
        # Base priority from intent
        reasoning.append(f"Base priority for {intent_type} intent")
        
        # Urgency indicators
        if urgent_matches:
            reasoning.append(f"Contains urgency indicators: {', '.join(urgent_matches)}")
        
        # Fraud indicators
        if fraud_matches:
            reasoning.append(f"Contains fraud/security indicators: {', '.join(fraud_matches)}")
        
        # High-value invoice
        if intent_type == "INVOICE":
            currency_pattern = r'[$€£]\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
            amounts = re.findall(currency_pattern, text)
            
            numeric_values = []
            for amount in amounts:
                # Remove currency symbol and commas
                cleaned = re.sub(r'[$€£,\s]', '', amount)
                try:
                    numeric_values.append(float(cleaned))
                except ValueError:
                    pass
            
            if numeric_values and max(numeric_values) > 10000:
                reasoning.append(f"High-value invoice (amount > 10,000)")
        
        return "; ".join(reasoning)
