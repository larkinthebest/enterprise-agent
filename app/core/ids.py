import uuid

def generate_trace_id() -> str:
    return f'tr_{uuid.uuid4().hex}'

def generate_run_id() -> str:
    return f'run_{uuid.uuid4().hex}'