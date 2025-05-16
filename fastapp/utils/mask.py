class MaskedClass:
    def __init__(self, original, mask):
        """
        初始化 MaskedClass，优先从 mask 获取属性，其次是 original。

        :param original: 原始对象（类或实例）
        :param mask: 掩码对象（类或实例），优先使用它的属性
        """
        self._original = original
        self._mask = mask

    def __getattr__(self, name):
        """
        优先从 mask 查找属性，未找到则去 original 查找。
        """
        if hasattr(self._mask, name):
            return getattr(self._mask, name)
        elif hasattr(self._original, name):
            return getattr(self._original, name)
        else:
            raise AttributeError(
                f"Attribute '{name}' not found in either mask or original object."
            )


class Mask:
    pass


if __name__ == "__main__":
    # 示例用法
    class Original:
        def __init__(self):
            self.value = 10
            self.common = "original"

        def say_hello(self):
            print("Hello from Original")

    class Mask:
        def __init__(self):
            self.value = 20
            self.mask_only = "secret"

        def say_hello(self):
            print("Hello from Mask")

        def say_goodbye(self):
            print("Goodbye from Mask")

    # 创建原始和掩码对象
    original = Original()
    mask = Mask()

    # 创建带掩码的包装类
    wrapped = MaskedClass(original, mask)

    # 测试属性访问
    print(wrapped.value)  # 应该输出 Mask 的 value: 20
    print(wrapped.common)  # 应该输出 Original 的 common: "original"
    print(wrapped.mask_only)  # 应该输出 Mask 的 mask_only: "secret"

    # 测试方法调用
    wrapped.say_hello()  # 应该调用 Mask 的 say_hello
    wrapped.say_goodbye()  # 应该调用 Mask 的 say_goodbye
