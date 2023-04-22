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


class YouTubeMusicSearchError(Exception):
    def __init__(self: YouTubeMusicSearchError, message: str) -> None:
        super().__init__(f"Error searching YouTube Music: {message!r}")


class YouTubeMusicNoOverlayError(Exception):
    def __init__(self: YouTubeMusicNoOverlayError) -> None:
        super().__init__("No overlay found in song or video data.")
