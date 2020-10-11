from django.shortcuts import render, redirect
from myapp.models import Stock, UserProfile, FavoriteStock
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import QueryDict

from django.core.files.storage import FileSystemStorage
import pathlib


def fav_stock(request):
    if request.method == 'PUT':
        if not request.user.is_authenticated:
            return
        user = request.user
        put = QueryDict(request.body)
        stock_symbol = put.get('symbol')
        stock = Stock.objects.get(symbol=stock_symbol)
        try:
            favorite_stock = FavoriteStock.objects.get(user_id=user.id)
        except Exception as e:
            favorite_stock = FavoriteStock.objects.create(user_id=user.id)
            favorite_stock.save()
        favorite_stock.stocks.add(stock)
        favorite_stock.save()
        data = {}
        return JsonResponse(data)
    if request.method == 'DELETE':
        if not request.user.is_authenticated:
            return
        user = request.user
        put = QueryDict(request.body)
        stock_symbol = put.get('symbol')
        stock = Stock.objects.get(symbol=stock_symbol)
        favorite_stock = FavoriteStock.objects.get(user_id=user.id)
        favorite_stock.stocks.remove(stock)
        favorite_stock.save()
        data = {}
        return JsonResponse(data)
