"""Errors raised by circuit validation and the simulation engine."""


class CircuitRejected(ValueError):
    """A submitted circuit is outside the published application bounds."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.message = message


class EngineUnavailable(RuntimeError):
    """The configured engine could not evaluate a valid circuit."""
