from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Проверяем, является ли пользователь автором объекта
        return obj.author == request.user


class AuthorAdminOrReadOnly(BasePermission):
    message = 'Может быть отредактировано только автором или администратором'

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated
            and request.user.is_active
            and (request.user == obj.author or request.user.is_staff)

        )


class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
