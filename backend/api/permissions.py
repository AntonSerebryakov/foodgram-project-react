from rest_framework.permissions import SAFE_METHODS, BasePermission


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
