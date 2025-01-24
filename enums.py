from enum import Enum

class UserType(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"