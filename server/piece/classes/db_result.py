from enum import Enum

class DBResult:
    def __init__(self, content, code, message):
        self.content = content
        self.code = code
        self.message = message

class DBResultCode(Enum):
    OK = 1
    NOT_FOUND = 2
    ERROR = 3