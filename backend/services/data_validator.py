"""
Data Validator Service
Validates data formats, checks quality, handles missing values
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Type
from datetime import datetime
import re
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationError:
    """Represents a validation error"""
    
    def __init__(
        self,
        field: str,
        message: str,
        severity: ValidationSeverity,
        value: Any = None
    ):
        self.field = field
        self.message = message
        self.severity = severity
        self.value = value
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'field': self.field,
            'message': self.message,
            'severity': self.severity.value,
            'value': str(self.value) if self.value is not None else None,
            'timestamp': self.timestamp.isoformat()
        }


class DataValidator:
    """Validates data quality and format"""
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.errors: List[ValidationError] = []
    
    def reset(self) -> None:
        """Reset validation errors"""
        self.errors = []
    
    def add_error(
        self,
        field: str,
        message: str,
        severity: ValidationSeverity,
        value: Any = None
    ) -> None:
        """Add a validation error"""
        error = ValidationError(field, message, severity, value)
        self.errors.append(error)
        
        log_level = {
            ValidationSeverity.INFO: logging.INFO,
            ValidationSeverity.WARNING: logging.WARNING,
            ValidationSeverity.ERROR: logging.ERROR,
            ValidationSeverity.CRITICAL: logging.CRITICAL
        }[severity]
        
        logger.log(log_level, f"Validation {severity.value}: {field} - {message}")
    
    def has_errors(self) -> bool:
        """Check if there are validation errors"""
        if self.strict_mode:
            return any(e.severity in [ValidationSeverity.WARNING, ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                      for e in self.errors)
        return any(e.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                  for e in self.errors)
    
    def get_errors(self, min_severity: ValidationSeverity = ValidationSeverity.INFO) -> List[ValidationError]:
        """Get errors above minimum severity"""
        severity_order = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.ERROR: 2,
            ValidationSeverity.CRITICAL: 3
        }
        min_level = severity_order[min_severity]
        return [e for e in self.errors if severity_order[e.severity] >= min_level]
    
    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> bool:
        """Validate that required fields are present"""
        valid = True
        for field in required_fields:
            if field not in data or data[field] is None:
                self.add_error(
                    field,
                    f"Required field '{field}' is missing",
                    ValidationSeverity.ERROR
                )
                valid = False
        return valid
    
    def validate_field_type(
        self,
        data: Dict[str, Any],
        field: str,
        expected_type: Union[Type, Tuple[Type, ...]]
    ) -> bool:
        """Validate field type"""
        if field not in data:
            return True  # Skip if field doesn't exist
        
        value = data[field]
        if value is None:
            return True  # None is acceptable
        
        if not isinstance(value, expected_type):
            if isinstance(expected_type, tuple):
                type_name = ' or '.join(t.__name__ for t in expected_type)
            else:
                type_name = expected_type.__name__
            self.add_error(
                field,
                f"Expected type {type_name}, got {type(value).__name__}",
                ValidationSeverity.ERROR,
                value
            )
            return False
        return True
    
    def validate_numeric_range(
        self,
        data: Dict[str, Any],
        field: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> bool:
        """Validate numeric field is within range"""
        if field not in data or data[field] is None:
            return True
        
        value = data[field]
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                self.add_error(
                    field,
                    f"Value {num_value} is below minimum {min_value}",
                    ValidationSeverity.ERROR,
                    value
                )
                return False
            
            if max_value is not None and num_value > max_value:
                self.add_error(
                    field,
                    f"Value {num_value} exceeds maximum {max_value}",
                    ValidationSeverity.ERROR,
                    value
                )
                return False
            
            return True
        except (ValueError, TypeError):
            self.add_error(
                field,
                f"Cannot convert '{value}' to numeric",
                ValidationSeverity.ERROR,
                value
            )
            return False
    
    def validate_string_pattern(
        self,
        data: Dict[str, Any],
        field: str,
        pattern: str
    ) -> bool:
        """Validate string matches regex pattern"""
        if field not in data or data[field] is None:
            return True
        
        value = str(data[field])
        if not re.match(pattern, value):
            self.add_error(
                field,
                f"Value '{value}' does not match pattern '{pattern}'",
                ValidationSeverity.ERROR,
                value
            )
            return False
        return True
    
    def validate_enum(
        self,
        data: Dict[str, Any],
        field: str,
        allowed_values: List[Any]
    ) -> bool:
        """Validate field value is in allowed list"""
        if field not in data or data[field] is None:
            return True
        
        value = data[field]
        if value not in allowed_values:
            self.add_error(
                field,
                f"Value '{value}' not in allowed values: {allowed_values}",
                ValidationSeverity.ERROR,
                value
            )
            return False
        return True
    
    def validate_date_format(
        self,
        data: Dict[str, Any],
        field: str,
        date_format: str = '%Y-%m-%d'
    ) -> bool:
        """Validate date string format"""
        if field not in data or data[field] is None:
            return True
        
        value = data[field]
        if isinstance(value, datetime):
            return True
        
        try:
            datetime.strptime(str(value), date_format)
            return True
        except ValueError:
            self.add_error(
                field,
                f"Invalid date format. Expected '{date_format}', got '{value}'",
                ValidationSeverity.ERROR,
                value
            )
            return False
    
    def handle_missing_values(
        self,
        data: Dict[str, Any],
        field: str,
        default_value: Any = None,
        strategy: str = 'default'
    ) -> Any:
        """
        Handle missing values
        
        Args:
            data: Data dictionary
            field: Field name
            default_value: Default value to use
            strategy: 'default', 'skip', or 'error'
            
        Returns:
            Processed value
        """
        if field in data and data[field] is not None:
            return data[field]
        
        if strategy == 'error':
            self.add_error(
                field,
                f"Missing value for field '{field}'",
                ValidationSeverity.ERROR
            )
            return None
        elif strategy == 'skip':
            self.add_error(
                field,
                f"Skipping missing value for field '{field}'",
                ValidationSeverity.INFO
            )
            return None
        else:  # default
            if default_value is not None:
                self.add_error(
                    field,
                    f"Using default value {default_value} for missing field '{field}'",
                    ValidationSeverity.INFO
                )
            return default_value
    
    def validate_market_data(self, data: Dict[str, Any]) -> bool:
        """Validate market data record"""
        self.reset()
        
        # Required fields
        required = ['asset_id', 'timestamp', 'close_price']
        self.validate_required_fields(data, required)
        
        # Field types
        self.validate_field_type(data, 'asset_id', str)
        self.validate_field_type(data, 'close_price', (int, float))
        self.validate_field_type(data, 'volume', (int, float))
        
        # Numeric ranges
        self.validate_numeric_range(data, 'close_price', min_value=0)
        self.validate_numeric_range(data, 'volume', min_value=0)
        
        # Price consistency
        if all(k in data for k in ['open_price', 'high_price', 'low_price', 'close_price']):
            try:
                high = float(data['high_price'])
                low = float(data['low_price'])
                open_p = float(data['open_price'])
                close = float(data['close_price'])
                
                if high < low:
                    self.add_error(
                        'high_price',
                        f"High price ({high}) cannot be less than low price ({low})",
                        ValidationSeverity.ERROR
                    )
                
                if open_p > high or open_p < low:
                    self.add_error(
                        'open_price',
                        f"Open price ({open_p}) outside high-low range",
                        ValidationSeverity.WARNING
                    )
                
                if close > high or close < low:
                    self.add_error(
                        'close_price',
                        f"Close price ({close}) outside high-low range",
                        ValidationSeverity.WARNING
                    )
            except (ValueError, TypeError):
                pass
        
        return not self.has_errors()
    
    def validate_transaction(self, data: Dict[str, Any]) -> bool:
        """Validate transaction record"""
        self.reset()
        
        # Required fields
        required = ['portfolio_id', 'asset_id', 'quantity', 'price', 'transaction_date']
        self.validate_required_fields(data, required)
        
        # Field types
        self.validate_field_type(data, 'portfolio_id', str)
        self.validate_field_type(data, 'asset_id', str)
        self.validate_field_type(data, 'quantity', (int, float))
        self.validate_field_type(data, 'price', (int, float))
        
        # Numeric ranges
        self.validate_numeric_range(data, 'quantity', min_value=0)
        self.validate_numeric_range(data, 'price', min_value=0)
        self.validate_numeric_range(data, 'fees', min_value=0)
        
        # Transaction type
        if 'transaction_type' in data:
            self.validate_enum(
                data,
                'transaction_type',
                ['buy', 'sell', 'transfer', 'dividend', 'split']
            )
        
        # Status
        if 'status' in data:
            self.validate_enum(
                data,
                'status',
                ['pending', 'completed', 'cancelled', 'failed']
            )
        
        return not self.has_errors()
    
    def validate_portfolio_position(self, data: Dict[str, Any]) -> bool:
        """Validate portfolio position record"""
        self.reset()
        
        # Required fields
        required = ['portfolio_id', 'asset_id', 'quantity', 'as_of_date']
        self.validate_required_fields(data, required)
        
        # Field types
        self.validate_field_type(data, 'portfolio_id', str)
        self.validate_field_type(data, 'asset_id', str)
        self.validate_field_type(data, 'quantity', (int, float))
        
        # Numeric ranges
        self.validate_numeric_range(data, 'quantity', min_value=0)
        self.validate_numeric_range(data, 'weight', min_value=0, max_value=1)
        
        # P&L consistency
        if all(k in data for k in ['average_cost', 'current_price', 'quantity', 'unrealized_pnl']):
            try:
                avg_cost = float(data['average_cost'])
                current = float(data['current_price'])
                qty = float(data['quantity'])
                pnl = float(data['unrealized_pnl'])
                
                expected_pnl = (current - avg_cost) * qty
                if abs(pnl - expected_pnl) > 0.01:  # Allow small rounding errors
                    self.add_error(
                        'unrealized_pnl',
                        f"P&L mismatch: expected {expected_pnl:.2f}, got {pnl:.2f}",
                        ValidationSeverity.WARNING
                    )
            except (ValueError, TypeError):
                pass
        
        return not self.has_errors()
    
    def validate_risk_calculation(self, data: Dict[str, Any]) -> bool:
        """Validate risk calculation record"""
        self.reset()
        
        # Required fields
        required = ['entity_id', 'entity_type', 'calculation_type', 'risk_score']
        self.validate_required_fields(data, required)
        
        # Field types
        self.validate_field_type(data, 'entity_id', str)
        self.validate_field_type(data, 'entity_type', str)
        self.validate_field_type(data, 'risk_score', (int, float))
        
        # Numeric ranges
        self.validate_numeric_range(data, 'risk_score', min_value=0, max_value=1)
        self.validate_numeric_range(data, 'confidence', min_value=0, max_value=1)
        self.validate_numeric_range(data, 'volatility', min_value=0)
        
        # Entity type
        self.validate_enum(
            data,
            'entity_type',
            ['portfolio', 'asset', 'counterparty', 'position']
        )
        
        return not self.has_errors()
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report"""
        errors_by_severity = {
            'info': [],
            'warning': [],
            'error': [],
            'critical': []
        }
        
        for error in self.errors:
            errors_by_severity[error.severity.value].append(error.to_dict())
        
        return {
            'total_errors': len(self.errors),
            'has_errors': self.has_errors(),
            'errors_by_severity': errors_by_severity,
            'summary': {
                'info': len(errors_by_severity['info']),
                'warning': len(errors_by_severity['warning']),
                'error': len(errors_by_severity['error']),
                'critical': len(errors_by_severity['critical'])
            }
        }


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    validator = DataValidator(strict_mode=False)
    
    # Test market data validation
    market_data = {
        'asset_id': 'AAPL',
        'timestamp': '2024-01-01',
        'open_price': 150.0,
        'high_price': 155.0,
        'low_price': 148.0,
        'close_price': 152.0,
        'volume': 1000000
    }
    
    if validator.validate_market_data(market_data):
        print("✓ Market data is valid")
    else:
        print("✗ Market data validation failed")
        report = validator.get_validation_report()
        print(f"Errors: {report['summary']}")
    
    # Test transaction validation
    transaction = {
        'portfolio_id': 'portfolio_001',
        'asset_id': 'AAPL',
        'quantity': 100,
        'price': 150.0,
        'transaction_date': '2024-01-01',
        'transaction_type': 'buy'
    }
    
    if validator.validate_transaction(transaction):
        print("✓ Transaction is valid")
    else:
        print("✗ Transaction validation failed")

# Made with Bob
