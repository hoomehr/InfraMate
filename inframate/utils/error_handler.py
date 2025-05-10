from typing import Dict, List, Optional, Callable, Tuple
import time
import logging
import os
import json
from dataclasses import dataclass
from enum import Enum

# Import Gemini API
try:
    import google.generativeai as genai
except ImportError:
    pass

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    error_type: str
    message: str
    severity: ErrorSeverity
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: float = 0
    recovery_strategy: Optional[str] = None
    ai_solution: Optional[str] = None
    context_data: Optional[Dict] = None

class AgentSupervisor:
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register a recovery strategy for a specific error type"""
        self.recovery_strategies[error_type] = strategy

    def should_retry(self, error_context: ErrorContext) -> bool:
        """Determine if an error should be retried based on context"""
        if error_context.retry_count >= error_context.max_retries:
            return False
            
        # Implement exponential backoff
        if error_context.last_attempt > 0:
            backoff = min(300, (2 ** error_context.retry_count) * 10)
            if time.time() - error_context.last_attempt < backoff:
                return False
                
        return True

class ErrorLoopHandler:
    def __init__(self):
        self.supervisor = AgentSupervisor()
        self.logger = logging.getLogger(__name__)
        self.gemini_model = self._initialize_gemini()
        
        # Register default recovery strategies
        self._register_default_strategies()
        
    def _initialize_gemini(self):
        """Initialize the Gemini API if available"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or 'genai' not in globals():
            self.logger.warning("Gemini API not available. AI-powered error handling disabled.")
            return None
            
        try:
            genai.configure(api_key=api_key)
            # Using the most capable model for error analysis
            return genai.GenerativeModel('gemini-1.5-pro')
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {str(e)}")
            return None
        
    def _register_default_strategies(self):
        """Register default error recovery strategies"""
        self.supervisor.register_recovery_strategy(
            "api_error",
            lambda ctx: self._handle_api_error(ctx)
        )
        self.supervisor.register_recovery_strategy(
            "terraform_error",
            lambda ctx: self._handle_terraform_error(ctx)
        )
        self.supervisor.register_recovery_strategy(
            "resource_conflict",
            lambda ctx: self._handle_resource_conflict(ctx)
        )
        self.supervisor.register_recovery_strategy(
            "gemini_error",
            lambda ctx: self._handle_gemini_error(ctx)
        )
        
    async def get_ai_solution(self, context: ErrorContext) -> Optional[str]:
        """Get an AI-powered solution for the error using Gemini"""
        if not self.gemini_model:
            return None
            
        try:
            # Prepare context data for AI analysis
            error_info = {
                "error_type": context.error_type,
                "error_message": context.message,
                "severity": context.severity.value,
                "retry_count": context.retry_count,
                "context_data": context.context_data or {}
            }
            
            # Create a detailed prompt for the AI
            prompt = f"""
            As an AI assistant specializing in infrastructure and deployment, analyze this error and provide a solution:
            
            ERROR DETAILS:
            {json.dumps(error_info, indent=2)}
            
            TASK:
            1. Identify the root cause of this error
            2. Provide a step-by-step solution to resolve it
            3. Suggest preventive measures to avoid similar errors in the future
            
            Format your response as a JSON with these keys:
            - root_cause: Brief explanation of what caused the error
            - solution: Step-by-step instructions to fix the issue
            - prevention: How to prevent this error in the future
            """
            
            # Get response from Gemini
            response = await self.gemini_model.generate_content_async(prompt)
            
            # Parse the response to extract the JSON
            try:
                solution = response.text
                # Extract just the JSON part if there's additional text
                if "{" in solution and "}" in solution:
                    start_idx = solution.find("{")
                    end_idx = solution.rfind("}") + 1
                    solution_json = json.loads(solution[start_idx:end_idx])
                    return solution_json
                return json.loads(solution)
            except json.JSONDecodeError:
                # If not valid JSON, return the raw text
                return {"solution": response.text}
                
        except Exception as e:
            self.logger.error(f"Failed to get AI solution: {str(e)}")
            return None
        
    def handle_error(self, error_type: str, message: str, severity: ErrorSeverity, context_data: Optional[Dict] = None) -> Tuple[bool, Optional[Dict]]:
        """Main error handling entry point, returns success status and solution"""
        context = ErrorContext(
            error_type=error_type,
            message=message,
            severity=severity,
            context_data=context_data
        )
        
        # Log the error
        self.logger.error(f"Error encountered: {error_type} - {message}")
        
        # Get AI solution asynchronously
        import asyncio
        try:
            ai_solution = asyncio.run(self.get_ai_solution(context))
            context.ai_solution = ai_solution
        except Exception as e:
            self.logger.error(f"Failed to get AI solution: {str(e)}")
        
        # Try builtin recovery strategies
        recovery_success = False
        recovery_result = None
        
        # Check if we have a recovery strategy
        if error_type in self.supervisor.recovery_strategies:
            strategy = self.supervisor.recovery_strategies[error_type]
            
            while self.supervisor.should_retry(context):
                try:
                    recovery_result = strategy(context)
                    if recovery_result:
                        self.logger.info(f"Successfully recovered from {error_type}")
                        recovery_success = True
                        break
                except Exception as e:
                    self.logger.error(f"Recovery attempt failed: {str(e)}")
                    
                context.retry_count += 1
                context.last_attempt = time.time()
        
        # If we get here and recovery failed, handle as unrecoverable
        if not recovery_success:
            self._handle_unrecoverable_error(context)
        
        # Add to error history regardless of outcome
        self.supervisor.error_history.append(context)
        
        # Return the status and solution
        return recovery_success, context.ai_solution
        
    def _handle_api_error(self, context: ErrorContext) -> Optional[str]:
        """Handle API-related errors"""
        if "rate_limit" in context.message.lower():
            time.sleep(60)  # Wait for rate limit to reset
            return "retry"
        return None
        
    def _handle_terraform_error(self, context: ErrorContext) -> Optional[str]:
        """Handle Terraform-specific errors"""
        if "state_lock" in context.message.lower():
            time.sleep(30)  # Wait for state lock to be released
            return "retry"
        return None
        
    def _handle_resource_conflict(self, context: ErrorContext) -> Optional[str]:
        """Handle resource conflicts"""
        if context.retry_count < 3:
            time.sleep(15)  # Wait for potential race conditions to resolve
            return "retry"
        return None
        
    def _handle_gemini_error(self, context: ErrorContext) -> Optional[str]:
        """Handle Gemini API errors"""
        if "quota" in context.message.lower():
            # If we hit quota issues, wait longer
            time.sleep(300)  # 5 minutes
            return "retry"
        return None
        
    def _handle_unrecoverable_error(self, context: ErrorContext):
        """Handle errors that couldn't be recovered from"""
        self.logger.critical(
            f"Unrecoverable error: {context.error_type}\n"
            f"Message: {context.message}\n"
            f"Severity: {context.severity}\n"
            f"Retry attempts: {context.retry_count}"
        )
        
    def get_error_report(self) -> Dict:
        """Generate a comprehensive error report"""
        report = {
            "errors": [],
            "total_error_count": len(self.supervisor.error_history),
            "recovered_count": 0,
            "unrecovered_count": 0
        }
        
        for error in self.supervisor.error_history:
            error_entry = {
                "type": error.error_type,
                "message": error.message,
                "severity": error.severity.value,
                "retry_count": error.retry_count,
                "ai_solution": error.ai_solution
            }
            
            report["errors"].append(error_entry)
            if error.retry_count < error.max_retries:
                report["recovered_count"] += 1
            else:
                report["unrecovered_count"] += 1
                
        return report 