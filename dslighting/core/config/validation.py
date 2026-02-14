"""
Configuration validation module.

Provides extensible config validation with custom validators support.
"""

from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field

# Import shared workflow names for validation
from .shared import VALID_WORKFLOW_NAMES


@dataclass
class ValidationError:
    """A single validation error."""
    field: str
    message: str
    severity: str = "error"
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def __post_init__(self):
        self.is_valid = len(self.errors) == 0

    def add_error(self, field: str, message: str, code: Optional[str] = None) -> None:
        """Add an error to the result."""
        self.errors.append(ValidationError(field=field, message=message, code=code))

    def add_warning(self, field: str, message: str, code: Optional[str] = None) -> None:
        """Add a warning to the result."""
        self.warnings.append(ValidationError(field=field, message=message, code=code))


class ConfigValidator:
    """Extensible config validation with custom validators.

    This class provides a framework for validating configuration dictionaries
    with support for custom validators and severity levels.

    Example:
        >>> validator = ConfigValidator()
        >>> validator.register_validator("required_fields", my_validator, "error")
        >>> result = validator.validate(config, schema_name="llm")
    """

    def __init__(self):
        self._validators: Dict[str, Dict] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_validators()
        self._register_builtin_schemas()

    def register_validator(
        self,
        name: str,
        fn: Callable,
        severity: str = "error",
        schema_name: Optional[str] = None
    ) -> None:
        """Register a custom validator.

        Args:
            name: Unique identifier for the validator.
            fn: Callable that takes (config, field_name) and returns
                (is_valid, message, code).
            severity: Severity level - "error" or "warning".
            schema_name: Optional schema name this validator applies to.
        """
        self._validators[name] = {
            "fn": fn,
            "severity": severity,
            "schema_name": schema_name
        }

    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a validation schema.

        Args:
            name: Schema name.
            schema: Schema definition with fields and validation rules.
        """
        self._schemas[name] = schema

    def validate(
        self,
        config: Dict[str, Any],
        schema_name: Optional[str] = None
    ) -> ValidationResult:
        """Validate a configuration dictionary.

        Args:
            config: Configuration dictionary to validate.
            schema_name: Optional schema name to use for validation.

        Returns:
            ValidationResult containing validation status, errors, and warnings.
        """
        result = ValidationResult(is_valid=True)

        # Run registered validators
        for name, validator_info in self._validators.items():
            fn = validator_info["fn"]
            severity = validator_info["severity"]
            validator_schema = validator_info.get("schema_name")

            # Skip if validator is schema-specific and doesn't match
            if validator_schema and validator_schema != schema_name:
                continue

            try:
                # Call validator - it can return a dict of errors or call result.add_*
                validation_output = fn(config)
                if isinstance(validation_output, dict):
                    for field_name, error_info in validation_output.items():
                        if isinstance(error_info, dict):
                            message = error_info.get("message", f"Validation failed for {field_name}")
                            code = error_info.get("code")
                            if severity == "error":
                                result.add_error(field_name, message, code)
                            else:
                                result.add_warning(field_name, message, code)
                        else:
                            if severity == "error":
                                result.add_error(field_name, str(error_info))
                            else:
                                result.add_warning(field_name, str(error_info))
            except Exception as e:
                result.add_error(name, f"Validator error: {str(e)}")

        # Apply schema validation if available
        if schema_name and schema_name in self._schemas:
            schema_errors = self._apply_schema(config, self._schemas[schema_name])
            result.errors.extend(schema_errors)

        return result

    def _apply_schema(
        self,
        config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> list[ValidationError]:
        """Apply a schema to validate configuration.

        Args:
            config: Configuration to validate.
            schema: Schema definition.

        Returns:
            List of validation errors.
        """
        errors = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    code="REQUIRED_FIELD"
                ))

        # Check field types
        field_types = schema.get("types", {})
        for field, expected_type in field_types.items():
            if field in config:
                value = config[field]
                if not isinstance(value, expected_type):
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}",
                        code="TYPE_MISMATCH"
                    ))

        # Check field constraints
        constraints = schema.get("constraints", {})
        for field, constraint_info in constraints.items():
            if field in config:
                value = config[field]
                if "min" in constraint_info and value < constraint_info["min"]:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be >= {constraint_info['min']}, got {value}",
                        code="CONSTRAINT_VIOLATION"
                    ))
                if "max" in constraint_info and value > constraint_info["max"]:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be <= {constraint_info['max']}, got {value}",
                        code="CONSTRAINT_VIOLATION"
                    ))
                if "choices" in constraint_info and value not in constraint_info["choices"]:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be one of {constraint_info['choices']}, got {value}",
                        code="INVALID_CHOICE"
                    ))

        return errors

    def _register_builtin_validators(self) -> None:
        """Register built-in validators."""
        # Required fields validator
        def required_fields_validator(config: Dict[str, Any]) -> Dict[str, Any]:
            required = config.get("_required_fields", [])
            errors = {}
            for field in required:
                if field not in config:
                    errors[field] = {"message": f"Required field '{field}' is missing", "code": "REQUIRED"}
            return errors

        self.register_validator("required_fields", required_fields_validator)

    def _register_builtin_schemas(self) -> None:
        """Register built-in schemas."""
        # LLM Config schema
        self._schemas["llm"] = {
            "required": ["model"],
            "types": {
                "model": str,
                "temperature": (int, float),
                "max_retries": int,
            },
            "constraints": {
                "temperature": {"min": 0.0, "max": 2.0},
                "max_retries": {"min": 0, "max": 10},
            }
        }

        # Run Config schema
        self._schemas["run"] = {
            "types": {
                "total_steps": int,
                "keep_all_workspaces": bool,
                "keep_workspace_on_failure": bool,
            },
            "constraints": {
                "total_steps": {"min": 1, "max": 100},
            }
        }

        # Workflow Config schema
        self._schemas["workflow"] = {
            "required": ["name"],
            "types": {
                "name": str,
            },
            "constraints": {
                "name": {"choices": list(VALID_WORKFLOW_NAMES)},
            }
        }
