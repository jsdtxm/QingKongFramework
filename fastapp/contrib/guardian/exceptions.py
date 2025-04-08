class GuardianError(Exception):
    pass


class NotUserNorGroup(GuardianError):
    pass


class ObjectNotPersisted(GuardianError):
    pass


class WrongAppError(GuardianError):
    pass


class MixedContentTypeError(GuardianError):
    pass


class MultipleIdentityAndObjectError(GuardianError):
    pass
