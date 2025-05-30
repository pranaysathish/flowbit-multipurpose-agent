import json
from typing import Dict, Any, List, Optional, Set
import re

class JSONAgent:
    """
    JSON Agent that parses webhook data, validates required schema fields,
    and flags anomalies like field mismatches or type errors.
    """
    
    def __init__(self, memory_store):
        self.memory_store = memory_store
        
        # Define common schema templates for validation
        self.schema_templates = {
            "webhook": {
                "required_fields": ["event_type", "timestamp", "data"],
                "field_types": {
                    "event_type": str,
                    "timestamp": str,
                    "data": dict
                }
            },
            "user": {
                "required_fields": ["id", "name", "email"],
                "field_types": {
                    "id": [str, int],  # Can be string or integer
                    "name": str,
                    "email": str
                }
            },
            "transaction": {
                "required_fields": ["id", "amount", "currency", "status"],
                "field_types": {
                    "id": [str, int],
                    "amount": [float, int],
                    "currency": str,
                    "status": str
                }
            },
            "order": {
                "required_fields": ["order_id", "customer_id", "items", "total"],
                "field_types": {
                    "order_id": [str, int],
                    "customer_id": [str, int],
                    "items": list,
                    "total": [float, int]
                }
            },
            "fraud_alert": {
                "required_fields": ["alert_type", "risk_level", "timestamp"],
                "field_types": {
                    "alert_type": str,
                    "risk_level": str,
                    "timestamp": str,
                    "transaction_id": [str, int],
                    "details": dict,
                    "recommended_action": str,
                    "confidence_score": [float, int]
                }
            },
            "invoice": {
                "required_fields": ["invoice_number", "amount", "date"],
                "field_types": {
                    "invoice_number": [str, int],
                    "amount": [float, int],
                    "date": str,
                    "due_date": str,
                    "customer": [str, dict],
                    "items": list
                }
            }
        }
    
    def process(self, request_id: str, content: Any) -> Dict[str, Any]:
        """
        Process JSON data to validate schema and flag anomalies
        
        Args:
            request_id: The unique identifier for the request
            content: The JSON content (dict, string, or bytes)
            
        Returns:
            Dict containing validation results and anomalies
        """
        # Parse JSON content if needed
        json_data = self._parse_json(content)
        
        # Identify schema template
        schema_name, schema_confidence = self._identify_schema(json_data)
        
        # Validate against schema
        validation_results = self._validate_schema(json_data, schema_name)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(json_data, schema_name)
        
        # Determine if alert is needed
        alert_needed = len(anomalies) > 0
        
        # Create result
        result = {
            "schema_identification": {
                "schema_name": schema_name,
                "confidence": schema_confidence
            },
            "validation_results": validation_results,
            "anomalies": anomalies,
            "alert_needed": alert_needed,
            "original_data": json_data  # Store the original data for reference
        }
        
        # Store processing result in memory
        self.memory_store.store_processing_result(request_id, "json_agent", result)
        
        # Add detailed trace
        self.memory_store.add_trace(
            request_id,
            "json_agent",
            "json_processing_details",
            {
                "schema_identification": {
                    "schema_name": schema_name,
                    "confidence": schema_confidence,
                    "matching_fields": self._get_matching_fields(json_data, schema_name)
                },
                "validation_details": validation_results,
                "anomaly_details": {
                    "count": len(anomalies),
                    "types": list(set(a["type"] for a in anomalies)) if anomalies else []
                }
            }
        )
        
        return result
    
    def _parse_json(self, content: Any) -> Dict[str, Any]:
        """Parse JSON content into a Python dictionary"""
        
        if isinstance(content, dict):
            return content
        
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If it's not valid JSON, wrap it in a simple structure
                return {"raw_content": content}
        
        if isinstance(content, bytes):
            try:
                return json.loads(content.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If it's not valid JSON or UTF-8, wrap it in a simple structure
                return {"raw_content": str(content)}
        
        # For any other type, convert to string and wrap
        return {"raw_content": str(content)}
    
    def _identify_schema(self, json_data: Dict[str, Any]) -> tuple:
        """
        Identify which schema template best matches the JSON data
        
        Returns:
            Tuple of (schema_name, confidence)
        """
        if not isinstance(json_data, dict):
            return "unknown", 0.0
        
        # Calculate match scores for each schema
        schema_scores = {}
        
        for schema_name, schema_def in self.schema_templates.items():
            required_fields = schema_def["required_fields"]
            
            # Count matching required fields
            matching_fields = [field for field in required_fields if field in json_data]
            
            # Calculate match percentage
            if required_fields:
                match_percentage = len(matching_fields) / len(required_fields)
            else:
                match_percentage = 0.0
            
            schema_scores[schema_name] = match_percentage
        
        # Find the schema with the highest score
        if not schema_scores:
            return "unknown", 0.0
        
        best_schema = max(schema_scores, key=schema_scores.get)
        confidence = schema_scores[best_schema]
        
        # If confidence is too low, return unknown
        if confidence < 0.5:
            return "unknown", confidence
        
        return best_schema, confidence
    
    def _validate_schema(self, json_data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Validate JSON data against the identified schema
        
        Returns:
            Dict containing validation results
        """
        if schema_name == "unknown" or schema_name not in self.schema_templates:
            return {
                "valid": False,
                "missing_fields": [],
                "type_errors": [],
                "message": "Unknown schema, cannot validate"
            }
        
        schema_def = self.schema_templates[schema_name]
        required_fields = schema_def["required_fields"]
        field_types = schema_def["field_types"]
        
        # Check for missing required fields
        missing_fields = [field for field in required_fields if field not in json_data]
        
        # Check for type errors
        type_errors = []
        for field, expected_type in field_types.items():
            if field in json_data:
                # Handle multiple allowed types
                if isinstance(expected_type, list):
                    if not any(isinstance(json_data[field], t) for t in expected_type):
                        actual_type = type(json_data[field]).__name__
                        expected_types = [t.__name__ for t in expected_type]
                        type_errors.append({
                            "field": field,
                            "expected_type": " or ".join(expected_types),
                            "actual_type": actual_type
                        })
                else:
                    if not isinstance(json_data[field], expected_type):
                        type_errors.append({
                            "field": field,
                            "expected_type": expected_type.__name__,
                            "actual_type": type(json_data[field]).__name__
                        })
        
        # Determine if valid
        valid = len(missing_fields) == 0 and len(type_errors) == 0
        
        # Create validation result
        validation_result = {
            "valid": valid,
            "missing_fields": missing_fields,
            "type_errors": type_errors,
            "message": "Validation successful" if valid else "Validation failed"
        }
        
        return validation_result
    
    def _detect_anomalies(self, json_data: Dict[str, Any], schema_name: str) -> List[Dict[str, Any]]:
        """
        Detect anomalies in the JSON data
        
        Returns:
            List of anomalies detected
        """
        anomalies = []
        
        # Skip anomaly detection for unknown schema
        if schema_name == "unknown" or schema_name not in self.schema_templates:
            return anomalies
        
        schema_def = self.schema_templates[schema_name]
        
        # Check for schema mismatch percentage
        if isinstance(json_data, dict):
            schema_fields = set(schema_def["field_types"].keys())
            data_fields = set(json_data.keys())
            
            # Fields in data but not in schema
            extra_fields = data_fields - schema_fields
            
            # Calculate mismatch percentage
            if schema_fields:
                mismatch_percentage = len(extra_fields) / len(schema_fields) * 100
                
                # Flag if mismatch is significant (>30%)
                if mismatch_percentage > 30:
                    anomalies.append({
                        "type": "schema_mismatch",
                        "description": f"Schema mismatch of {mismatch_percentage:.1f}%",
                        "details": {
                            "extra_fields": list(extra_fields),
                            "mismatch_percentage": mismatch_percentage
                        }
                    })
        
        # Check for missing critical fields
        missing_critical = []
        for field in schema_def["required_fields"]:
            if field not in json_data:
                missing_critical.append(field)
        
        if missing_critical:
            anomalies.append({
                "type": "missing_critical_fields",
                "description": f"Missing {len(missing_critical)} critical fields",
                "details": {
                    "missing_fields": missing_critical
                }
            })
        
        # Check for type inconsistencies
        type_errors = []
        for field, expected_type in schema_def["field_types"].items():
            if field in json_data:
                # Handle multiple allowed types
                if isinstance(expected_type, list):
                    if not any(isinstance(json_data[field], t) for t in expected_type):
                        type_errors.append(field)
                else:
                    if not isinstance(json_data[field], expected_type):
                        type_errors.append(field)
        
        if type_errors:
            anomalies.append({
                "type": "type_inconsistencies",
                "description": f"Type inconsistencies in {len(type_errors)} fields",
                "details": {
                    "fields_with_errors": type_errors
                }
            })
        
        # Check for suspicious patterns
        suspicious_patterns = self._check_suspicious_patterns(json_data)
        if suspicious_patterns:
            anomalies.append({
                "type": "suspicious_patterns",
                "description": f"Found {len(suspicious_patterns)} suspicious patterns",
                "details": {
                    "patterns": suspicious_patterns
                }
            })
        
        return anomalies
    
    def _check_suspicious_patterns(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for suspicious patterns in the JSON data"""
        suspicious_patterns = []
        
        # Function to recursively check values in the JSON data
        def check_values(data, path=""):
            if isinstance(data, dict):
                # Check for fraud risk indicators at the top level
                if path == "" and "alert_type" in data and isinstance(data["alert_type"], str):
                    if "risk" in data["alert_type"].lower() or "fraud" in data["alert_type"].lower():
                        suspicious_patterns.append({
                            "path": "alert_type",
                            "value": data["alert_type"],
                            "reason": "Fraud risk alert detected"
                        })
                
                # Check for high risk level
                if path == "" and "risk_level" in data and isinstance(data["risk_level"], str):
                    if data["risk_level"].lower() in ["high", "critical", "severe"]:
                        suspicious_patterns.append({
                            "path": "risk_level",
                            "value": data["risk_level"],
                            "reason": "High risk level detected"
                        })
                
                # Check for suspicious recommended actions
                if path == "" and "recommended_action" in data and isinstance(data["recommended_action"], str):
                    if data["recommended_action"].lower() in ["block", "reject", "escalate", "investigate"]:
                        suspicious_patterns.append({
                            "path": "recommended_action",
                            "value": data["recommended_action"],
                            "reason": "Suspicious recommended action"
                        })
                
                # Check for high confidence score
                if path == "" and "confidence_score" in data and isinstance(data["confidence_score"], (float, int)):
                    if data["confidence_score"] > 0.8:
                        suspicious_patterns.append({
                            "path": "confidence_score",
                            "value": data["confidence_score"],
                            "reason": "High confidence score for risk"
                        })
                
                # Check for risk factors list
                if "risk_factors" in data and isinstance(data["risk_factors"], list) and len(data["risk_factors"]) > 0:
                    current_path = f"{path}.risk_factors" if path else "risk_factors"
                    suspicious_patterns.append({
                        "path": current_path,
                        "value": ", ".join(str(factor) for factor in data["risk_factors"]),
                        "reason": f"Risk factors detected: {len(data['risk_factors'])}"
                    })
                
                # Check for unusual location
                if "location" in data and isinstance(data["location"], dict):
                    location_path = f"{path}.location" if path else "location"
                    if "country" in data["location"] and data["location"]["country"] in ["RU", "KP", "IR", "SY"]:
                        suspicious_patterns.append({
                            "path": f"{location_path}.country",
                            "value": data["location"]["country"],
                            "reason": "Potentially high-risk country code"
                        })
                
                # Process each key-value pair
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check for SQL injection patterns
                    if isinstance(value, str) and any(pattern in value.lower() for pattern in 
                                                    ["select ", "insert ", "update ", "delete ", "drop ", 
                                                     "union ", "--", "1=1", "or 1=1"]):
                        suspicious_patterns.append({
                            "path": current_path,
                            "value": value,
                            "reason": "Potential SQL injection"
                        })
                    
                    # Check for script injection
                    if isinstance(value, str) and any(pattern in value.lower() for pattern in 
                                                    ["<script>", "javascript:", "onerror=", "onload="]):
                        suspicious_patterns.append({
                            "path": current_path,
                            "value": value,
                            "reason": "Potential script injection"
                        })
                    
                    # Check for unusually long strings
                    if isinstance(value, str) and len(value) > 1000:
                        suspicious_patterns.append({
                            "path": current_path,
                            "value": value[:50] + "...",  # Truncate for readability
                            "reason": "Unusually long string"
                        })
                    
                    # Check for large transaction amounts
                    if key in ["amount", "total"] and isinstance(value, (int, float)) and value > 10000:
                        suspicious_patterns.append({
                            "path": current_path,
                            "value": value,
                            "reason": "Large transaction amount"
                        })
                    
                    # Recursively check nested values
                    check_values(value, current_path)
                    
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    current_path = f"{path}[{i}]"
                    check_values(item, current_path)
        
        # Start recursive check
        if isinstance(json_data, dict):
            check_values(json_data)
        
        return suspicious_patterns
    
    def _get_matching_fields(self, json_data: Dict[str, Any], schema_name: str) -> List[str]:
        """Get the fields that match the identified schema"""
        
        if schema_name == "unknown" or schema_name not in self.schema_templates:
            return []
        
        schema_def = self.schema_templates[schema_name]
        required_fields = schema_def["required_fields"]
        
        matching_fields = [field for field in required_fields if field in json_data]
        return matching_fields
