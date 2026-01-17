"""认证异常"""


class AuthenticationError(Exception):
    """认证失败"""


class EmailAlreadyExistsError(AuthenticationError):
    """邮箱已被注册"""

    def __init__(self, message: str = "邮箱已被注册"):
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """邮箱或密码错误"""

    def __init__(self, message: str = "邮箱或密码错误"):
        super().__init__(message)


class UserNotFoundError(AuthenticationError):
    """用户不存在"""

    def __init__(self, message: str = "用户不存在"):
        super().__init__(message)


class UserDisabledError(AuthenticationError):
    """用户已被禁用"""

    def __init__(self, message: str = "用户已被禁用"):
        super().__init__(message)


class UserNameSameError(AuthenticationError):
    """用户名和原用户名相同"""

    def __init__(self, message: str = "用户名和原用户名相同"):
        super().__init__(message)


class UserEmailSameError(AuthenticationError):
    """邮箱和原邮箱相同"""

    def __init__(self, message: str = "邮箱和原邮箱相同"):
        super().__init__(message)


class UserPasswordSameError(AuthenticationError):
    """密码和原密码相同"""

    def __init__(self, message: str = "密码和原密码相同"):
        super().__init__(message)


class ExpiredTokenError(AuthenticationError):
    """令牌已过期"""

    def __init__(self, message: str = "令牌已过期"):
        super().__init__(message)


class InsufficientPermissionsError(AuthenticationError):
    """权限不足"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message)


class InvalidAccessTokenError(AuthenticationError):
    """无效访问令牌"""

    def __init__(self, message: str = "无效访问令牌"):
        super().__init__(message)


class InvalidRefreshTokenError(AuthenticationError):
    """无效刷新令牌"""

    def __init__(self, message: str = "无效刷新令牌"):
        super().__init__(message)
