from libs.requests import DjangoStyleRequest


class OperationHolderMixin:
    def __and__(self, other):
        return OperandHolder(AND, self, other)

    def __or__(self, other):
        return OperandHolder(OR, self, other)

    def __rand__(self, other):
        return OperandHolder(AND, other, self)

    def __ror__(self, other):
        return OperandHolder(OR, other, self)

    def __invert__(self):
        return SingleOperandHolder(NOT, self)


class SingleOperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class):
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        return self.operator_class(op1)


class OperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class, op2_class):
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        op2 = self.op2_class(*args, **kwargs)
        return self.operator_class(op1, op2)

    def __eq__(self, other):
        return (
            isinstance(other, OperandHolder)
            and self.operator_class == other.operator_class
            and self.op1_class == other.op1_class
            and self.op2_class == other.op2_class
        )

    def __hash__(self):
        return hash((self.operator_class, self.op1_class, self.op2_class))


class AND:
    def __init__(self, op1: "BasePermission", op2: "BasePermission"):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request: DjangoStyleRequest, view):
        return self.op1.has_permission(request, view) and self.op2.has_permission(
            request, view
        )

    def has_object_permission(self, request: DjangoStyleRequest, view, obj):
        return self.op1.has_object_permission(
            request, view, obj
        ) and self.op2.has_object_permission(request, view, obj)


class OR:
    def __init__(self, op1: "BasePermission", op2: "BasePermission"):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request: DjangoStyleRequest, view):
        return self.op1.has_permission(request, view) or self.op2.has_permission(
            request, view
        )

    def has_object_permission(self, request: DjangoStyleRequest, view, obj):
        return (
            self.op1.has_permission(request, view)
            and self.op1.has_object_permission(request, view, obj)
        ) or (
            self.op2.has_permission(request, view)
            and self.op2.has_object_permission(request, view, obj)
        )


class NOT:
    def __init__(self, op1: "BasePermission"):
        self.op1 = op1

    def has_permission(self, request: DjangoStyleRequest, view):
        return not self.op1.has_permission(request, view)

    def has_object_permission(self, request: DjangoStyleRequest, view, obj):
        return not self.op1.has_object_permission(request, view, obj)


class BasePermissionMetaclass(OperationHolderMixin, type):
    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, request: DjangoStyleRequest, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, request: DjangoStyleRequest, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True
