import json
import requests
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

class ActionRouter:
    """
    Action Router that triggers follow-up actions based on agent outputs.
    Simulates external API calls for actions like creating tickets, escalating issues, or flagging compliance risks.
    """
    
    def __init__(self, memory_store):
        self.memory_store = memory_store
        
        # Define action endpoints (simulated)
        self.action_endpoints = {
            "CREATE_TICKET": "/crm/tickets",
            "ESCALATE_ISSUE": "/crm/tickets",  # Same endpoint but different payload
            "FLAG_COMPLIANCE": "/compliance/logs",
            "RISK_ALERT": "/risk/alerts",
            "LOG_ONLY": None  # No endpoint needed for log-only actions
        }
        
        # Base URL for simulated API calls
        self.base_url = "http://localhost:8000"  # Will be handled by the same FastAPI app
    
    def route_action(self, request_id: str, classification: Dict[str, Any], processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to appropriate action based on classification and processing results
        
        Args:
            request_id: The unique identifier for the request
            classification: The classification results from the classifier agent
            processing_result: The processing results from the format-specific agent
            
        Returns:
            Dict containing action results
        """
        # Determine required action based on classification and processing results
        action_type, action_data = self._determine_action(classification, processing_result)
        
        # Execute the action
        action_result = self._execute_action(action_type, action_data)
        
        # Store action result in memory
        self.memory_store.store_action_result(request_id, action_result)
        
        # Add detailed trace
        self.memory_store.add_trace(
            request_id,
            "action_router",
            "action_routing_details",
            {
                "determined_action": action_type,
                "action_reasoning": self._get_action_reasoning(classification, processing_result, action_type),
                "action_result": action_result
            }
        )
        
        return action_result
    
    def _determine_action(self, classification: Dict[str, Any], processing_result: Dict[str, Any]) -> tuple:
        """
        Determine the required action based on classification and processing results
        
        Returns:
            Tuple of (action_type, action_data)
        """
        format_type = classification.get("format")
        intent_type = classification.get("intent")
        priority = classification.get("priority", "LOW")
        
        action_data = {
            "timestamp": datetime.now().isoformat(),
            "classification": classification,
            "processing_result": processing_result
        }
        
        # Determine action based on format type and processing results
        if format_type == "EMAIL":
            return self._determine_email_action(processing_result, intent_type, priority, action_data)
        elif format_type == "JSON":
            return self._determine_json_action(processing_result, intent_type, priority, action_data)
        elif format_type == "PDF":
            return self._determine_pdf_action(processing_result, intent_type, priority, action_data)
        else:
            # Default action for unknown format
            return "LOG_ONLY", action_data
    
    def _determine_email_action(self, processing_result: Dict[str, Any], intent_type: str, priority: str, action_data: Dict[str, Any]) -> tuple:
        """Determine action for email input"""
        
        analysis = processing_result.get("analysis", {})
        tone = analysis.get("tone", "NEUTRAL")
        urgency = analysis.get("urgency", "LOW")
        action_required = analysis.get("action_required", "LOG_AND_CLOSE")
        
        # Prepare action data
        action_data.update({
            "tone": tone,
            "urgency": urgency,
            "intent_type": intent_type
        })
        
        # Map email agent's action to router action
        if action_required == "ESCALATE_TO_CRM":
            # Create an escalated ticket in CRM
            ticket_data = {
                "type": "ESCALATION",
                "priority": priority,
                "subject": processing_result.get("structured_fields", {}).get("subject", "Email Escalation"),
                "description": f"Escalated email from {processing_result.get('structured_fields', {}).get('sender', 'Unknown')}",
                "tone": tone,
                "urgency": urgency
            }
            action_data["ticket_data"] = ticket_data
            return "ESCALATE_ISSUE", action_data
        else:
            # Just log the email
            return "LOG_ONLY", action_data
    
    def _determine_json_action(self, processing_result: Dict[str, Any], intent_type: str, priority: str, action_data: Dict[str, Any]) -> tuple:
        """Determine action for JSON input"""
        
        alert_needed = processing_result.get("alert_needed", False)
        anomalies = processing_result.get("anomalies", [])
        schema_info = processing_result.get("schema_identification", {})
        
        # Prepare action data
        action_data.update({
            "anomalies": anomalies,
            "intent_type": intent_type,
            "schema_info": schema_info
        })
        
        # Special handling for fraud risk intent
        if intent_type == "FRAUD_RISK":
            # Extract original JSON data if available
            original_data = {}
            if "validation_results" in processing_result:
                # Try to extract key fields from the original data
                if "alert_type" in processing_result.get("original_data", {}):
                    original_data = processing_result.get("original_data", {})
            
            # Create a risk alert with high priority
            alert_data = {
                "type": "FRAUD_RISK_ALERT",
                "priority": "HIGH",  # Override to HIGH for fraud risks
                "risk_level": original_data.get("risk_level", "unknown"),
                "transaction_id": original_data.get("transaction_id", "unknown"),
                "recommended_action": original_data.get("recommended_action", "investigate"),
                "confidence_score": original_data.get("confidence_score", 0),
                "description": "Potential fraud risk detected in transaction"
            }
            action_data["alert_data"] = alert_data
            return "RISK_ALERT", action_data
        
        # If schema is fraud_alert, create a risk alert regardless of anomalies
        if schema_info.get("schema_name") == "fraud_alert" and schema_info.get("confidence", 0) > 0.5:
            alert_data = {
                "type": "FRAUD_ALERT_SCHEMA",
                "priority": priority,
                "schema": schema_info.get("schema_name"),
                "confidence": schema_info.get("confidence"),
                "description": "Fraud alert schema detected in JSON data"
            }
            action_data["alert_data"] = alert_data
            return "RISK_ALERT", action_data
        
        # If anomalies are detected, create a risk alert
        if alert_needed and anomalies:
            # Check for suspicious patterns related to fraud
            fraud_related_anomalies = []
            for anomaly in anomalies:
                if anomaly.get("type") == "suspicious_patterns":
                    patterns = anomaly.get("details", {}).get("patterns", [])
                    for pattern in patterns:
                        if any(term in pattern.get("reason", "").lower() for term in 
                              ["fraud", "risk", "suspicious", "unusual", "high risk", "large amount"]):
                            fraud_related_anomalies.append(pattern)
            
            # If fraud-related anomalies are found, escalate to RISK_ALERT
            if fraud_related_anomalies:
                alert_data = {
                    "type": "FRAUD_RISK_PATTERNS",
                    "priority": "HIGH",  # Override to HIGH for fraud risks
                    "anomaly_count": len(fraud_related_anomalies),
                    "patterns": fraud_related_anomalies,
                    "description": f"Detected {len(fraud_related_anomalies)} fraud risk patterns in JSON data"
                }
                action_data["alert_data"] = alert_data
                return "RISK_ALERT", action_data
            
            # For other anomalies
            anomaly_types = [anomaly.get("type") for anomaly in anomalies]
            
            alert_data = {
                "type": "JSON_ANOMALY",
                "priority": priority,
                "anomaly_types": anomaly_types,
                "description": f"Detected {len(anomalies)} anomalies in JSON data"
            }
            action_data["alert_data"] = alert_data
            return "RISK_ALERT", action_data
        else:
            # Just log the JSON processing
            return "LOG_ONLY", action_data
    
    def _determine_pdf_action(self, processing_result: Dict[str, Any], intent_type: str, priority: str, action_data: Dict[str, Any]) -> tuple:
        """Determine action for PDF input"""
        
        document_type = processing_result.get("document_type", "GENERAL")
        flags = processing_result.get("flags", [])
        alert_needed = processing_result.get("alert_needed", False)
        
        # Prepare action data
        action_data.update({
            "document_type": document_type,
            "flags": flags,
            "intent_type": intent_type
        })
        
        # Check for compliance flags
        compliance_flags = [flag for flag in flags if "compliance" in flag.get("type", "").lower()]
        
        # Check for high-value invoice
        high_value_flags = [flag for flag in flags if flag.get("type") == "high_value_invoice"]
        
        if compliance_flags:
            # Log compliance issue
            compliance_data = {
                "type": "COMPLIANCE_FLAG",
                "priority": priority,
                "flags": compliance_flags,
                "description": f"Detected {len(compliance_flags)} compliance flags in PDF document"
            }
            action_data["compliance_data"] = compliance_data
            return "FLAG_COMPLIANCE", action_data
        elif high_value_flags:
            # Create ticket for high-value invoice
            ticket_data = {
                "type": "HIGH_VALUE_INVOICE",
                "priority": priority,
                "flags": high_value_flags,
                "description": "High-value invoice requires approval"
            }
            action_data["ticket_data"] = ticket_data
            return "CREATE_TICKET", action_data
        elif alert_needed and flags:
            # Create general alert for other flags
            alert_data = {
                "type": "PDF_FLAGS",
                "priority": priority,
                "flags": flags,
                "description": f"Detected {len(flags)} flags in PDF document"
            }
            action_data["alert_data"] = alert_data
            return "RISK_ALERT", action_data
        else:
            # Just log the PDF processing
            return "LOG_ONLY", action_data
    
    def _execute_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the determined action (simulated API call)
        
        Returns:
            Dict containing action execution results
        """
        endpoint = self.action_endpoints.get(action_type)
        
        # For LOG_ONLY actions, no API call needed
        if action_type == "LOG_ONLY" or not endpoint:
            return {
                "action_type": action_type,
                "status": "completed",
                "message": "Action logged only, no external API call required",
                "timestamp": datetime.now().isoformat()
            }
        
        # Prepare result with default values
        result = {
            "action_type": action_type,
            "endpoint": endpoint,
            "status": "failed",
            "message": "Action execution failed",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # In a real implementation, this would make an actual API call
            # For simulation, we'll just prepare the response as if the call succeeded
            
            # Simulate API call based on action type
            if action_type == "CREATE_TICKET" or action_type == "ESCALATE_ISSUE":
                ticket_id = str(uuid.uuid4())
                result.update({
                    "status": "completed",
                    "message": f"Ticket created successfully with ID: {ticket_id}",
                    "ticket_id": ticket_id,
                    "ticket_data": action_data.get("ticket_data", {})
                })
            
            elif action_type == "FLAG_COMPLIANCE":
                log_id = str(uuid.uuid4())
                result.update({
                    "status": "completed",
                    "message": f"Compliance issue logged successfully with ID: {log_id}",
                    "log_id": log_id,
                    "compliance_data": action_data.get("compliance_data", {})
                })
            
            elif action_type == "RISK_ALERT":
                alert_id = str(uuid.uuid4())
                result.update({
                    "status": "completed",
                    "message": f"Risk alert created successfully with ID: {alert_id}",
                    "alert_id": alert_id,
                    "alert_data": action_data.get("alert_data", {})
                })
        
        except Exception as e:
            # Handle any exceptions during action execution
            result.update({
                "status": "failed",
                "message": f"Action execution failed: {str(e)}",
                "error": str(e)
            })
        
        return result
    
    def _get_action_reasoning(self, classification: Dict[str, Any], processing_result: Dict[str, Any], action_type: str) -> str:
        """Get reasoning for the determined action"""
        
        format_type = classification.get("format")
        intent_type = classification.get("intent")
        priority = classification.get("priority", "LOW")
        
        reasoning_parts = []
        
        # Add format and intent context
        reasoning_parts.append(f"Input format: {format_type}")
        reasoning_parts.append(f"Business intent: {intent_type}")
        reasoning_parts.append(f"Priority: {priority}")
        
        # Add format-specific reasoning
        if format_type == "EMAIL":
            analysis = processing_result.get("analysis", {})
            tone = analysis.get("tone", "NEUTRAL")
            urgency = analysis.get("urgency", "LOW")
            
            reasoning_parts.append(f"Email tone: {tone}")
            reasoning_parts.append(f"Email urgency: {urgency}")
            
            if action_type == "ESCALATE_ISSUE":
                if tone in ["THREATENING", "ESCALATION"]:
                    reasoning_parts.append(f"Escalation required due to {tone.lower()} tone")
                if urgency == "HIGH":
                    reasoning_parts.append("Escalation required due to high urgency")
        
        elif format_type == "JSON":
            anomalies = processing_result.get("anomalies", [])
            
            if action_type == "RISK_ALERT" and anomalies:
                anomaly_types = [anomaly.get("type") for anomaly in anomalies]
                reasoning_parts.append(f"Risk alert created due to detected anomalies: {', '.join(anomaly_types)}")
        
        elif format_type == "PDF":
            document_type = processing_result.get("document_type", "GENERAL")
            flags = processing_result.get("flags", [])
            
            reasoning_parts.append(f"PDF document type: {document_type}")
            
            if action_type == "FLAG_COMPLIANCE":
                reasoning_parts.append("Compliance flagging required due to detected compliance references")
            
            elif action_type == "CREATE_TICKET" and document_type == "INVOICE":
                reasoning_parts.append("Ticket created for high-value invoice that requires approval")
            
            elif action_type == "RISK_ALERT" and flags:
                flag_types = [flag.get("type") for flag in flags]
                reasoning_parts.append(f"Risk alert created due to detected flags: {', '.join(flag_types)}")
        
        return "; ".join(reasoning_parts)
