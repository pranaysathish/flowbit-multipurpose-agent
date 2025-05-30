import re
import email
from email import policy
from email.parser import BytesParser, Parser
from typing import Dict, Any, List, Optional
import json

class EmailAgent:
    """
    Email Agent that extracts structured fields from emails and identifies tone.
    Triggers actions based on tone and urgency.
    """
    
    def __init__(self, memory_store):
        self.memory_store = memory_store
        
        # Define tone categories and their indicators
        self.tone_indicators = {
            "ESCALATION": [
                "escalate", "urgent", "immediately", "supervisor", "manager", 
                "unacceptable", "demand", "insist", "higher level"
            ],
            "POLITE": [
                "please", "thank you", "appreciate", "grateful", "kindly", 
                "regards", "sincerely", "respectfully"
            ],
            "THREATENING": [
                "legal action", "lawyer", "attorney", "sue", "lawsuit", "court", 
                "legal", "consequences", "deadline", "ultimatum", "or else"
            ],
            "ANGRY": [
                "angry", "upset", "furious", "outraged", "disappointed", "frustrated",
                "terrible", "horrible", "worst", "never", "unacceptable", "ridiculous"
            ],
            "NEUTRAL": []  # Default tone
        }
    
    def process(self, request_id: str, content: Any) -> Dict[str, Any]:
        """
        Process an email to extract structured fields and identify tone
        
        Args:
            request_id: The unique identifier for the request
            content: The email content (string or bytes)
            
        Returns:
            Dict containing extracted fields and analysis
        """
        # Parse email content
        email_data = self._parse_email(content)
        
        # Extract structured fields
        structured_fields = self._extract_structured_fields(email_data)
        
        # Identify tone
        tone = self._identify_tone(email_data)
        
        # Determine urgency
        urgency = self._determine_urgency(email_data, tone)
        
        # Determine required action
        action = self._determine_action(tone, urgency)
        
        # Create result
        result = {
            "structured_fields": structured_fields,
            "analysis": {
                "tone": tone,
                "urgency": urgency,
                "action_required": action
            }
        }
        
        # Store processing result in memory
        self.memory_store.store_processing_result(request_id, "email_agent", result)
        
        # Add detailed trace
        self.memory_store.add_trace(
            request_id,
            "email_agent",
            "email_processing_details",
            {
                "tone_analysis": {
                    "detected_tone": tone,
                    "tone_indicators": self._get_matched_tone_indicators(email_data, tone)
                },
                "urgency_analysis": {
                    "urgency_level": urgency,
                    "urgency_indicators": self._get_urgency_indicators(email_data)
                },
                "action_determination": {
                    "action": action,
                    "reasoning": self._get_action_reasoning(tone, urgency)
                }
            }
        )
        
        return result
    
    def _parse_email(self, content: Any) -> Dict[str, Any]:
        """Parse email content into a structured format"""
        
        # Handle plain text emails that might not be in standard email format
        if isinstance(content, str) and not content.startswith('From:') and not content.startswith('To:'):
            # Check if this looks like a plain text email with headers
            if 'Subject:' in content or 'From:' in content:
                # Try to extract headers from plain text
                headers = {}
                body_lines = []
                header_section = True
                lines = content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if header_section:
                        if not line:  # Empty line marks end of headers
                            header_section = False
                            continue
                        
                        # Try to extract header
                        header_match = re.match(r'^([\w\-]+):\s*(.+)$', line)
                        if header_match:
                            key, value = header_match.groups()
                            headers[key.lower()] = value
                    else:
                        body_lines.append(line)
                
                return {
                    "headers": headers,
                    "body": '\n'.join(body_lines)
                }
            else:
                # Treat the entire content as body if no headers are found
                return {
                    "headers": {},
                    "body": content
                }
        
        # Standard email parsing for properly formatted emails
        try:
            if isinstance(content, bytes):
                # Parse email from bytes
                msg = BytesParser(policy=policy.default).parse(content)
            elif isinstance(content, str):
                # Parse email from string
                msg = Parser(policy=policy.default).parsestr(content)
            else:
                # Handle case where content is already parsed or in another format
                return {"headers": {}, "body": str(content)}
            
            # Extract headers
            headers = {}
            for key in msg.keys():
                headers[key.lower()] = msg[key]
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    # Get text content
                    if content_type == "text/plain":
                        body_part = part.get_payload(decode=True)
                        if isinstance(body_part, bytes):
                            body += body_part.decode('utf-8', errors='ignore')
                        else:
                            body += str(body_part)
            else:
                body_content = msg.get_payload(decode=True)
                if isinstance(body_content, bytes):
                    body = body_content.decode('utf-8', errors='ignore')
                else:
                    body = str(body_content)
        except Exception as e:
            # If parsing fails, treat the entire content as body
            print(f"Email parsing error: {str(e)}")
            return {
                "headers": {},
                "body": str(content)
            }
        
        return {
            "headers": headers,
            "body": body
        }
    
    def _extract_structured_fields(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured fields from email data"""
        
        headers = email_data.get("headers", {})
        body = email_data.get("body", "")
        
        # Extract basic fields
        structured_fields = {
            "sender": headers.get("from", ""),
            "recipient": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "cc": headers.get("cc", ""),
            "reply_to": headers.get("reply-to", "")
        }
        
        # Extract email addresses
        sender_email = self._extract_email_address(structured_fields["sender"])
        if sender_email:
            structured_fields["sender_email"] = sender_email
        
        # Extract issue/request from subject and body
        structured_fields["issue"] = self._extract_issue(structured_fields["subject"], body)
        
        # Extract any reference numbers or IDs
        structured_fields["reference_ids"] = self._extract_reference_ids(body)
        
        return structured_fields
    
    def _extract_email_address(self, text: str) -> str:
        """Extract email address from a text string"""
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)
        return ""
    
    def _extract_issue(self, subject: str, body: str) -> str:
        """Extract the main issue or request from subject and body"""
        
        # First try to use the subject as the issue
        if subject and len(subject) > 5:
            return subject
        
        # If subject is not useful, try to extract from first paragraph of body
        paragraphs = body.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 10:
                # Limit to first sentence or first 100 chars
                first_sentence = first_para.split('.')[0]
                if len(first_sentence) > 100:
                    return first_sentence[:100] + "..."
                return first_sentence
        
        return "Unknown issue"
    
    def _extract_reference_ids(self, body: str) -> List[str]:
        """Extract reference numbers or IDs from email body"""
        
        # Common patterns for reference IDs
        patterns = [
            r'reference\s*(?:number|#|id|code)?\s*[:#]?\s*([A-Z0-9]{5,})',
            r'order\s*(?:number|#|id)?\s*[:#]?\s*([A-Z0-9]{5,})',
            r'ticket\s*(?:number|#|id)?\s*[:#]?\s*([A-Z0-9]{5,})',
            r'case\s*(?:number|#|id)?\s*[:#]?\s*([A-Z0-9]{5,})',
            r'invoice\s*(?:number|#|id)?\s*[:#]?\s*([A-Z0-9]{5,})'
        ]
        
        reference_ids = []
        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            reference_ids.extend(matches)
        
        return list(set(reference_ids))  # Remove duplicates
    
    def _identify_tone(self, email_data: Dict[str, Any]) -> str:
        """Identify the tone of the email"""
        
        body = email_data.get("body", "")
        subject = email_data.get("headers", {}).get("subject", "")
        
        # Combine subject and body for analysis
        text = subject + " " + body
        text = text.lower()
        
        # Count matches for each tone
        tone_scores = {}
        for tone, indicators in self.tone_indicators.items():
            score = 0
            for indicator in indicators:
                # Count occurrences
                matches = len(re.findall(r'\b' + re.escape(indicator) + r'\b', text, re.IGNORECASE))
                score += matches
            
            tone_scores[tone] = score
        
        # Find the tone with the highest score
        max_score = max(tone_scores.values()) if tone_scores else 0
        
        # If no clear tone is detected, default to NEUTRAL
        if max_score == 0:
            return "NEUTRAL"
        
        # Get all tones with the max score
        max_tones = [tone for tone, score in tone_scores.items() if score == max_score]
        
        # Priority order for tones with equal scores
        priority_order = ["THREATENING", "ESCALATION", "ANGRY", "POLITE", "NEUTRAL"]
        
        # Return the highest priority tone among those with max score
        for tone in priority_order:
            if tone in max_tones:
                return tone
        
        return "NEUTRAL"
    
    def _determine_urgency(self, email_data: Dict[str, Any], tone: str) -> str:
        """Determine the urgency level of the email"""
        
        body = email_data.get("body", "")
        subject = email_data.get("headers", {}).get("subject", "")
        
        # Combine subject and body for analysis
        text = subject + " " + body
        text = text.lower()
        
        # Urgency indicators
        high_urgency_indicators = [
            "urgent", "immediately", "asap", "emergency", "critical",
            "as soon as possible", "right away", "time sensitive", "deadline",
            "today", "now", "priority"
        ]
        
        medium_urgency_indicators = [
            "soon", "timely", "promptly", "quickly", "expedite",
            "this week", "follow up", "important"
        ]
        
        # Count urgency indicators
        high_count = sum(1 for indicator in high_urgency_indicators if indicator in text)
        medium_count = sum(1 for indicator in medium_urgency_indicators if indicator in text)
        
        # Determine base urgency from indicators
        if high_count > 0:
            base_urgency = "HIGH"
        elif medium_count > 0:
            base_urgency = "MEDIUM"
        else:
            base_urgency = "LOW"
        
        # Adjust based on tone
        if tone in ["THREATENING", "ESCALATION"]:
            # Upgrade urgency for threatening or escalation tones
            if base_urgency == "LOW":
                return "MEDIUM"
            else:
                return "HIGH"
        elif tone == "ANGRY":
            # Slightly upgrade urgency for angry tone
            if base_urgency == "LOW":
                return "MEDIUM"
            else:
                return base_urgency
        else:
            return base_urgency
    
    def _determine_action(self, tone: str, urgency: str) -> str:
        """Determine the required action based on tone and urgency"""
        
        # High urgency or threatening/escalation tone requires escalation
        if urgency == "HIGH" or tone in ["THREATENING", "ESCALATION"]:
            return "ESCALATE_TO_CRM"
        
        # Medium urgency with angry tone also requires escalation
        if urgency == "MEDIUM" and tone == "ANGRY":
            return "ESCALATE_TO_CRM"
        
        # All other cases are routine
        return "LOG_AND_CLOSE"
    
    def _get_matched_tone_indicators(self, email_data: Dict[str, Any], detected_tone: str) -> List[str]:
        """Get the indicators that matched for the detected tone"""
        
        body = email_data.get("body", "")
        subject = email_data.get("headers", {}).get("subject", "")
        
        # Combine subject and body for analysis
        text = subject + " " + body
        text = text.lower()
        
        matched_indicators = []
        
        if detected_tone in self.tone_indicators:
            for indicator in self.tone_indicators[detected_tone]:
                if re.search(r'\b' + re.escape(indicator) + r'\b', text, re.IGNORECASE):
                    matched_indicators.append(indicator)
        
        return matched_indicators
    
    def _get_urgency_indicators(self, email_data: Dict[str, Any]) -> List[str]:
        """Get the urgency indicators found in the email"""
        
        body = email_data.get("body", "")
        subject = email_data.get("headers", {}).get("subject", "")
        
        # Combine subject and body for analysis
        text = subject + " " + body
        text = text.lower()
        
        # All urgency indicators
        all_urgency_indicators = [
            "urgent", "immediately", "asap", "emergency", "critical",
            "as soon as possible", "right away", "time sensitive", "deadline",
            "today", "now", "priority", "soon", "timely", "promptly", 
            "quickly", "expedite", "this week", "follow up", "important"
        ]
        
        # Find matches
        matched_indicators = []
        for indicator in all_urgency_indicators:
            if re.search(r'\b' + re.escape(indicator) + r'\b', text, re.IGNORECASE):
                matched_indicators.append(indicator)
        
        return matched_indicators
    
    def _get_action_reasoning(self, tone: str, urgency: str) -> str:
        """Get reasoning for the determined action"""
        
        if urgency == "HIGH" and tone in ["THREATENING", "ESCALATION"]:
            return "High urgency combined with threatening/escalation tone requires immediate escalation"
        elif urgency == "HIGH":
            return "High urgency requires escalation regardless of tone"
        elif tone in ["THREATENING", "ESCALATION"]:
            return f"{tone.capitalize()} tone requires escalation regardless of urgency"
        elif urgency == "MEDIUM" and tone == "ANGRY":
            return "Medium urgency combined with angry tone requires escalation"
        else:
            return "Standard urgency and tone can be handled through normal process"
