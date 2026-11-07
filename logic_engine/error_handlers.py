import logging
from datetime import datetime


class LogicEngineBaseError(Exception):
    """Base exception for all Logic Engine errors."""
    pass

class ConfigurationError(LogicEngineBaseError):
    """Raised when the config file is missing or corrupted."""
    pass

class DataValidationError(LogicEngineBaseError):
    """Raised when incoming database records have negative or missing critical values."""
    pass

class DatabaseConnectionError(LogicEngineBaseError):
    """Raised when the database cannot be read."""
    pass

class ErrorManager:
    """Catches errors, logs them safely, and returns a fallback dictionary."""
    
    def __init__(self, log_filepath: str = "logic_engine_errors.log"):
        self.logger = logging.getLogger("LogicEngineErrorManager")
        self.logger.setLevel(logging.ERROR)
        
        # Setup file handler
        handler = logging.FileHandler(log_filepath)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def handle_exception(self, error: Exception, context: str) -> dict:
        """Logs the error and returns an empty fallback state for the AI/Dashboard."""
        error_msg = f"Failure in {context}: {str(error)}"
        self.logger.error(error_msg)
        
        # Return a safe fallback dictionary so the system doesn't completely crash
        return {
            "run_timestamp": datetime.now().isoformat(timespec="seconds"),
            "status": "FAILED",
            "error_message": error_msg,
            "total_energy_kwh": 0.0,
            "total_cost_usd": 0.0,
            "total_carbon_kg": 0.0,
            "sustainability_score": 0.0,
            "category_breakdown_kwh": {},
            "peak_demands_detected": []
        }
