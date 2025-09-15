class MemoryException(Exception):
    pass


class BadAddressException(MemoryException):
    pass


class OutOfMemoryException(MemoryException):
    pass


class RegisterException(Exception):
    pass
