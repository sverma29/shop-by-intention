"""
Event Context Management

Holds thread-local or global context for event tracing, specifically `session_id` / `trace_id`.
"""
import uuid
import threading

_event_context = threading.local()

def set_session_id(session_id: str = None) -> str:
    """Set the current session ID for tracing events. If None, generates a new one."""
    if not session_id:
        session_id = str(uuid.uuid4())
    _event_context.session_id = session_id
    return session_id

def get_session_id() -> str:
    """Get the current session ID, generating a default one if none exists."""
    if not hasattr(_event_context, "session_id"):
        _event_context.session_id = str(uuid.uuid4())
    return _event_context.session_id
