from typing import Dict, List, Optional, Callable
import time
import logging
from dataclasses import dataclass
from enum import Enum

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
        
        # Register default recovery strategies
        self._register_default_strategies()
        
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
        
    def handle_error(self, error_type: str, message: str, severity: ErrorSeverity) -> Optional[str]:
        """Main error handling entry point"""
        context = ErrorContext(
            error_type=error_type,
            message=message,
            severity=severity
        )
        
        # Log the error
        self.logger.error(f"Error encountered: {error_type} - {message}")
        
        # Check if we have a recovery strategy
        if error_type in self.supervisor.recovery_strategies:
            strategy = self.supervisor.recovery_strategies[error_type]
            
            while self.supervisor.should_retry(context):
                try:
                    recovery_result = strategy(context)
                    if recovery_result:
                        self.logger.info(f"Successfully recovered from {error_type}")
                        return recovery_result
                except Exception as e:
                    self.logger.error(f"Recovery attempt failed: {str(e)}")
                    
                context.retry_count += 1
                context.last_attempt = time.time()
                
        # If we get here, all retries failed or no strategy exists
        self._handle_unrecoverable_error(context)
        return None
        
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
        
    def _handle_unrecoverable_error(self, context: ErrorContext):
        """Handle errors that couldn't be recovered from"""
        self.logger.critical(
            f"Unrecoverable error: {context.error_type}\n"
            f"Message: {context.message}\n"
            f"Severity: {context.severity}\n"
            f"Retry attempts: {context.retry_count}"
        )
        # Add to error history for analysis
        self.supervisor.error_history.append(context) 