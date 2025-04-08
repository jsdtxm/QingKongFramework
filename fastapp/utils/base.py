def class_override(obj, klass):
    obj.__class__ = klass
    return obj