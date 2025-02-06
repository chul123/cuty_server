from enum import Enum

class UserType(str, Enum):
    USER = "USER"     # 일반 사용자
    ADMIN = "ADMIN"   # 관리자 