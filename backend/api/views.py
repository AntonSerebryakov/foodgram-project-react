from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import IngredientSearch, RecipeFilter
from .models import (Fav, Ingredient, Recipe, RecipeIngredient, ShoppingList,
                     Subscription, Tag)
from .permissions import AuthorAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (CustomUserCreateSerializer, IngredientSerializer,
                          MiniRecipeSerializer, RecipeCreateSerializer,
                          RecipeListSerializer, SubscribeSerializer,
                          TagSerializer, UserInfoSerializer,
                          UserSubscribesSerializer)
from .utils import CustomPaginator

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = [AuthorAdminOrReadOnly, ]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientSearch


class UserCustomViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        return UserInfoSerializer

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = user.subscriber.all()
        authors = [subscription.author for subscription in subscriptions]
        paginated_queryset = self.paginate_queryset(authors)
        serializer = UserSubscribesSerializer(
            paginated_queryset,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscribeSerializer
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={
                    'user': request.user.id,
                    'author': id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(author=author, user=self.request.user)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        subscription = Subscription.objects.filter(user=request.user,
                                                   author=author)
        if subscription.exists():
            subscription.delete()
            return Response(
                {'message': 'Вы отписались от автора.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'message': 'Вы не подписаны на автора'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],)
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Пароль успешно изменен.'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Текущий пароль неверный.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeListSerializer

    @action(
        methods=('POST', 'DELETE',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            if Fav.objects.filter(user=request.user, recipe__id=pk).exists():
                return Response({'message': 'Рецепт уже в избранном!'},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                recipe = Recipe.objects.get(id=pk)
            except Recipe.DoesNotExist:
                return Response({'message': 'Рецепт не найден'},
                                status=status.HTTP_400_BAD_REQUEST)
            fav_item = Fav(user=request.user, recipe=recipe)
            fav_item.save()
            serializer = MiniRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not Recipe.objects.filter(id=pk).exists():
                return Response(status=status.HTTP_404_NOT_FOUND)
            instance = Fav.objects.filter(user=request.user, recipe__id=pk)
            if instance:
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('POST', 'DELETE',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):

        if request.method == 'POST':
            if ShoppingList.objects.filter(user=request.user,
                                           recipe__id=pk).exists():
                return Response({'message': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                recipe = Recipe.objects.get(id=pk)
            except Recipe.DoesNotExist:
                return Response({'message': 'Рецепт не найден'},
                                status=status.HTTP_400_BAD_REQUEST)
            shopping_list_item = ShoppingList(user=request.user, recipe=recipe)
            shopping_list_item.save()
            serializer = MiniRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not Recipe.objects.filter(id=pk).exists():
                return Response(status=status.HTTP_404_NOT_FOUND)
            instance = ShoppingList.objects.filter(user=request.user,
                                                   recipe__id=pk)
            if instance:
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('GET',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_reciep__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by('ingredient__name').annotate(Sum('amount'))
        shopping_list_text = 'Список покупок:\n'
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            amount = ingredient['amount__sum']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shopping_list_text += f'{name} - {amount} {measurement_unit}\n'
        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response
