import uuid

def new_session_id() -> str:
    """Generate a random 8 char session hex."""
    return uuid.uuid4().hex

def new_plan_id() -> str:
    """Generate a plan identifier."""
    return str(uuid.uuid4())
