from rest_framework.permissions import BasePermission


class ClientPermission(BasePermission):
    """登录权限校验"""

    def has_permission(self, request, view):
        """让所有用户都有权限"""
        return True

    def has_object_permission(self, request, view, obj):
        """用户是否有权限访问添加了权限控制类的数据对象"""
        # 需求，其他的不能够访问
        return True

