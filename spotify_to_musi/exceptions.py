from __future__ import annotations


class UnsupportedPlatformError(RuntimeError):
    """Raised when the platform is not supported."""

    def __init__(self: UnsupportedPlatformError, platform: str) -> None:
        super().__init__(f"Unsupported platform: {platform}")


class EmptyTupleError(ValueError):
    """Raised when a tuple is empty."""

    def __init__(self: EmptyTupleError, tuple_name: str) -> None:
        super().__init__(f"{tuple_name.capitalize()!r} can't be empty")


class BlankNameError(ValueError):
    """Raised when a name is blank."""

    def __init__(self: BlankNameError, name: str) -> None:
        super().__init__(f"{name.capitalize()!r} name can't be blank")
