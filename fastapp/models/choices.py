from collections import namedtuple
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fastapp.utils.functional import classproperty

T = TypeVar("T", int, str)


# 定义ChoiceItem用于存储标签，元类会将其转换为Choice对象
class ChoiceItem(Generic[T]):
    __slots__ = ("label",)

    value: T

    def __init__(self, label: str):
        self.label = label


# 使用具名元组来保存最终的选项值
Choice = namedtuple("Choice", ["value", "label"])


class ChoicesMeta(type):
    """实现Choices功能的元类"""

    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> Any:
        # 预处理类属性，转换ChoiceItem为Choice对象
        processed_namespace = {}
        choices = []

        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, ChoiceItem):
                # 将ChoiceItem转换为包含实际值（属性名）和标签的Choice对象
                choice = Choice(value=attr_name, label=attr_value.label)
                processed_namespace[attr_name] = choice
                choices.append(choice)
            else:
                processed_namespace[attr_name] = attr_value

        # 添加预计算的值集合
        processed_namespace["_choices"] = choices  # type: ignore
        processed_namespace["_values"] = tuple(c.value for c in choices)  # type: ignore
        processed_namespace["_labels"] = tuple(c.label for c in choices)  # type: ignore

        # 创建新的类对象
        cls = super().__new__(mcs, name, bases, processed_namespace)
        cls._frozen = True

        return cls

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False) and name not in {
            "__parameters__",
            "_frozen",
        }:
            raise AttributeError(
                f"Cannot add new attributes to {self.__class__.__name__}"
            )
        super().__setattr__(name, value)

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """禁止实例化"""
        raise TypeError(f"Cannot instantiate Choices class '{cls.__name__}'")


class Choices(Generic[T], metaclass=ChoicesMeta):
    """基础类，使用元类实现Choices功能"""

    @classproperty
    def values(cls) -> tuple[T]:
        return cls._values  # type: ignore

    @classproperty
    def labels(cls) -> tuple[str]:
        return cls._labels  # type: ignore

    if TYPE_CHECKING:

        @classmethod
        @property
        def values(cls) -> tuple[T]: ...

        @classmethod
        @property
        def labels(cls) -> tuple[str]: ...


if __name__ == "__main__":

    class ActionChoices(Choices[str]):
        CREATE = ChoiceItem("创建")
        REVOKE = ChoiceItem("撤销")

    # 访问单个选项
    print(ActionChoices.CREATE.value)  # 输出: 'CREATE'
    print(ActionChoices.CREATE.label)  # 输出: '创建'

    # 获取所有预计算的值
    print(ActionChoices.values)  # 输出: ('CREATE', 'REVOKE')
    print(ActionChoices.labels)  # 输出: ('创建', '撤销')

    # 以下操作都会抛出异常
    try:
        ActionChoices.NEW = ChoiceItem("新")  # 禁止动态添加属性
    except AttributeError as e:
        print(e)

    try:
        instance = ActionChoices()  # 禁止实例化
    except TypeError as e:
        print(e)
