import json
import requests
from typing import Dict, Any, List, Optional, Tuple
import uuid
import logging
from datetime import datetime
from app.utils.retry import retry_on_failure, RetryContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    def _determine_action(self, classification: Dict[str, Any], processing_result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
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
    
    def _determine_email_action(self, processing_result: Dict[str, Any], intent_type: str, priority: str, action_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Determine action for email input"""
        
        analysis = processing_result.get("analysis", {})
        tone = analysis.get("tone", "NEUTRAL")
        urgency = analysis.get("urgency", "LOW")
        action_required = analysis.get("action_required", "LOG_AND_CLOSE")
        
        # Prepare action data
        action_data.update({
            "tone": tone,
            "urgency": urgency,
            "action_required": action_required
        })
        
        # Determine action based on tone, urgency, and intent
        if tone in ["THREATENING", "ESCALATION"] or urgency == "HIGH" or intent_type == "COMPLAINT":
            # Escalate the issue
            ticket_data = {
                "type": "ESCALATION",
                "priority": priority,
                "tone": tone,
                "urgency": urgency,
                "description": "Customer issue requires immediate attention"
            }
            action_data["ticket_data"] = ticket_data
            return "ESCALATE_ISSUE", action_data
        
        elif intent_type == "RFQ" or action_required == "CREATE_TICKET":
            # Create a standard ticket
            ticket_data = {
                "type": "STANDARD",
                "priority": priority,
                "tone": tone,
                "urgency": urgency,
                "description": "Customer request requires follow-up"
            }
            action_data["ticket_data"] = ticket_data
            return "CREATE_TICKET", action_data
        
        elif intent_type == "FRAUD_RISK":
            # Create a risk alert
            alert_data = {
                "type": "FRAUD_ALERT",
                "priority": priority,
                "description": "Potential fraud risk detected in email"
            }
            action_data["alert_data"] = alert_data
            return "RISK_ALERT", action_data
        
        else:
            # Just log the email
            return "LOG_ONLY", action_data
    
    def _determine_json_action(self, processing_result: Dict[str, Any], intent_type: str, priority: str, action_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Determine action for JSON input"""
        
        anomalies = processing_result.get("anomalies", [])
        schema_valid = processing_result.get("schema_valid", True)
        
        # Prepare action data
        action_data.update({
            "schema_valid": schema_valid,
            "anomalies": anomalies
        })
        
        # Check for anomalies that might indicate fraud
        if not schema_valid or (anomalies and len(anomalies) > 0):
            # Create a risk alert for anomalies
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
    
    def _determine_pdf_action(self, processing_result: Dict[str, Any], intent_type: str, priority: str, action_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
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
    
    @retry_on_failure(max_retries=3, retry_delay=1.0, backoff_factor=2.0, exceptions=(requests.RequestException, ConnectionError, TimeoutError))
    def _make_api_call(self, action_type: str, endpoint: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an API call with retry logic
        
        Args:
            action_type: Type of action to execute
            endpoint: API endpoint to call
            action_data: Data to send with the API call
            
        Returns:
            Dict containing API call results
        """
        logger.info(f"Making API call for action: {action_type} to endpoint: {endpoint}")
        
        # In a real system, this would be an actual HTTP request
        # For simulation, we'll generate a response as if the call succeeded
        
        # Simulate API call
        if action_type == "CREATE_TICKET" or action_type == "ESCALATE_ISSUE":
            ticket_id = str(uuid.uuid4())
            return {
                "status": "completed",
                "message": f"Ticket created successfully with ID: {ticket_id}",
                "ticket_id": ticket_id,
                "ticket_data": action_data.get("ticket_data", {}),
                "retry_info": {"attempts": 1, "success": True}
            }
        
        elif action_type == "FLAG_COMPLIANCE":
            log_id = str(uuid.uuid4())
            return {
                "status": "completed",
                "message": f"Compliance issue logged successfully with ID: {log_id}",
                "log_id": log_id,
                "compliance_data": action_data.get("compliance_data", {}),
                "retry_info": {"attempts": 1, "success": True}
            }
        
        elif action_type == "RISK_ALERT":
            alert_id = str(uuid.uuid4())
            return {
                "status": "completed",
                "message": f"Risk alert created successfully with ID: {alert_id}",
                "alert_id": alert_id,
                "alert_data": action_data.get("alert_data", {}),
                "retry_info": {"attempts": 1, "success": True}
            }
        
        # Default case - should not reach here
        return {
            "status": "failed",
            "message": f"Unknown action type: {action_type}",
            "retry_info": {"attempts": 1, "success": False}
        }
    
    def _execute_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the determined action (simulated API call) with retry logic
        
        Returns:
            Dict containing action execution results
        """
        result = {
            "action_type": action_type,
            "timestamp": datetime.now().isoformat(),
        }
        
        # For LOG_ONLY action, no API call needed
        if action_type == "LOG_ONLY":
            result.update({
                "status": "completed",
                "message": "Information logged successfully",
                "retry_info": {"attempts": 0, "success": True}
            })
            return result
        
        # Get the endpoint for the action
        endpoint = self.action_endpoints.get(action_type)
        if not endpoint:
            result.update({
                "status": "failed",
                "message": f"Unknown action type: {action_type}",
                "retry_info": {"attempts": 0, "success": False}
            })
            return result
        
        # Use RetryContext for more complex retry scenarios
        with RetryContext(f"execute_{action_type}", max_retries=3, retry_delay=1.0, backoff_factor=2.0) as retry_ctx:
            try:
                # Try to execute the action with the retry decorator
                api_result = self._make_api_call(action_type, endpoint, action_data)
                result.update(api_result)
                
                # Add retry information to the result
                if "retry_info" not in result:
                    result["retry_info"] = {"attempts": retry_ctx.retry_count + 1, "success": True}
                
            except Exception as e:
                # Handle any exceptions during action execution
                logger.error(f"Action execution failed after {retry_ctx.retry_count + 1} attempts: {str(e)}")
                result.update({
                    "status": "failed",
                    "message": f"Action execution failed: {str(e)}",
                    "error": str(e),
                    "retry_info": {"attempts": retry_ctx.retry_count + 1, "success": False}
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
