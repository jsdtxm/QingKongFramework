from pypika.terms import Criterion, Term


def json_endswith(field: Term, value: str) -> Criterion:
    # will be override in each executor
    pass
