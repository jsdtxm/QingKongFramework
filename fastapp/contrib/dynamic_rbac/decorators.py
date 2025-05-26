def action_perm_decorator(perm):
    def wrap(func):
        func._perm = perm
        return func

    return wrap


def action_perm_target_decorator(target):
    def wrap(func):
        func._target = target
        return func

    return wrap


def action_dynamic_permission_decorator(perm=None, target=None):
    def wrap(func):
        func._perm = perm
        func._target = target
        return func

    return wrap
