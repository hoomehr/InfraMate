import unittest
from unittest.mock import patch
import time
from inframate.utils.error_handler import ErrorLoopHandler, ErrorSeverity

class TestErrorLoopHandler(unittest.TestCase):
    def setUp(self):
        self.handler = ErrorLoopHandler()

    def test_api_error_recovery(self):
        # Test rate limit error recovery
        result = self.handler.handle_error(
            "api_error",
            "Rate limit exceeded",
            ErrorSeverity.MEDIUM
        )
        self.assertEqual(result, "retry")

    def test_terraform_error_recovery(self):
        # Test terraform state lock error recovery
        result = self.handler.handle_error(
            "terraform_error",
            "state_lock could not be acquired",
            ErrorSeverity.HIGH
        )
        self.assertEqual(result, "retry")

    def test_unrecoverable_error(self):
        # Test handling of unrecoverable error
        result = self.handler.handle_error(
            "unknown_error",
            "This is an unknown error",
            ErrorSeverity.CRITICAL
        )
        self.assertIsNone(result)

    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_backoff(self, mock_sleep):
        # Test exponential backoff
        for _ in range(4):  # Trigger multiple retries
            self.handler.handle_error(
                "resource_conflict",
                "Resource is locked",
                ErrorSeverity.MEDIUM
            )
        
        # Verify exponential backoff was attempted
        mock_sleep.assert_called()

if __name__ == '__main__':
    unittest.main() 