from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as AbstractUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import IngredientSearch, RecipeFilter
from .models import (FavRecipes, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Subscription, Tag)
from .permissions import AuthorAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (IngredientSerializer,
                          MiniRecipeSerializer, RecipeCreateSerializer,
                          RecipeListSerializer, SubscribeSerializer,
                          TagSerializer,
                          UserSubscribesSerializer, FavRecipeCreateSerializer, ShoppingListSerializer)
from .utils import CustomPaginator

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = (AuthorAdminOrReadOnly, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None 
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientSearch


class UserViewSet(AbstractUserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPaginator

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

        deleted_count, _ = subscription.delete()
        if deleted_count > 0:
            return Response(
                {'message': 'Вы отписались от автора.'},
                status=status.HTTP_204_NO_CONTENT
                )
    
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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

    def add_to_selected(self,serializerClass, request, pk):
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'message': 'Рецепт не найден'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        serializer = serializerClass(data={'user': user.id, 'recipe': recipe.id},
                                     context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def del_selected(self, objectClass, request, pk):    
        get_object_or_404(Recipe, id=pk)
        instance = objectClass.objects.filter(user=request.user, recipe__id=pk)
        deleted_count, _ =instance.delete()
        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('POST', 'DELETE',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        
        if request.method == 'POST':
            return (self.add_to_selected(FavRecipeCreateSerializer, request, pk))
            
        elif request.method == 'DELETE':
            return self.del_selected(FavRecipes, request, pk)

    @action(
        methods=('POST', 'DELETE',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):

        if request.method == 'POST':
            return (self.add_to_selected(ShoppingListSerializer, request, pk))

        elif request.method == 'DELETE':
            return self.del_selected(ShoppingList, request, pk)


    @action(
        methods=('GET',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppinglist__user=request.user
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
