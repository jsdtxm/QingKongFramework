from typing import Self, Type


class OperableBase:
    _sources: tuple[Type[Self], ...]
    _operation: str


class OperableMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        if OperableBase not in bases and name != "OperableBase":
            raise TypeError(f"Class {name} must inherit from OperableBase")
        return super().__new__(mcs, name, bases, namespace)

    def __or__(cls: Type[OperableBase], other: "OperableMeta"):
        if not isinstance(other, OperableMeta):
            return NotImplemented
        # 生成新类名
        new_name = f"{cls.__name__}_OR_{other.__name__}"
        # 创建新类，继承自 OperableBase
        new_cls = OperableMeta(
            new_name,
            (OperableBase,),
            {
                "_sources": (cls, other),
                "_operation": "|",
            },
        )
        return new_cls

    def __and__(cls, other: "OperableMeta") -> "OperableMeta":
        if not isinstance(other, OperableMeta):
            return NotImplemented
        new_name = f"{cls.__name__}_AND_{other.__name__}"
        new_cls = OperableMeta(
            new_name,
            (OperableBase,),
            {
                "_sources": (cls, other),
                "_operation": "&",
            },
        )
        return new_cls

    def __xor__(cls, other: "OperableMeta") -> "OperableMeta":
        if not isinstance(other, OperableMeta):
            return NotImplemented
        new_name = f"{cls.__name__}_XOR_{other.__name__}"
        new_cls = OperableMeta(
            new_name,
            (OperableBase,),
            {
                "_sources": (cls, other),
                "_operation": "^",
            },
        )
        return new_cls

    def __invert__(cls) -> "OperableMeta":
        # TODO 避免重复取反：~~A 应该简化？这里暂不简化，保留结构
        new_name = f"NOT_{cls.__name__}"
        new_cls = OperableMeta(
            new_name,
            (OperableBase,),
            {
                "_sources": (cls,),
                "_operation": "~",
            },
        )
        return new_cls

    def __repr__(cls: Type[OperableBase]):
        if hasattr(cls, "_sources"):
            op = cls._operation
            if op == "~":
                # 一元：~A
                inner = cls._sources[0].__name__
                return f"<OperableClass {cls.__name__} (from ~{inner})>"
            else:
                # 二元：A | B
                names = f" {op} ".join(c.__name__ for c in cls._sources)
                return f"<OperableClass {cls.__name__} (from {names})>"
        return super().__repr__()


if __name__ == "__main__":

    class A(OperableBase, metaclass=OperableMeta):
        pass

    class B(OperableBase, metaclass=OperableMeta):
        pass

    class C(OperableBase, metaclass=OperableMeta):
        pass

    # 基本 OR
    D = A | B
    print(D)  # <OperableClass A_OR_B (from A | B)>

    # AND
    E = A & C
    print(E)  # <OperableClass A_AND_C (from A & C)>

    # XOR
    F = B ^ C
    print(F)  # <OperableClass B_XOR_C (from B ^ C)>

    # NOT
    G = ~A
    print(G)  # <OperableClass NOT_A (from ~A)>

    # 混合运算
    H = (A & B) | (~C)
    print(H)  # <OperableClass A_AND_B_OR_NOT_C (from A_AND_B | NOT_C)>

    # 验证继承关系
    assert issubclass(D, OperableBase)
    assert issubclass(H, OperableBase)

    # 属性检查
    print("H._operation:", H._operation)  # |
    print("H._sources:", H._sources)  # (A_AND_B, NOT_C)
