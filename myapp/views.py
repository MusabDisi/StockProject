import pathlib
from datetime import datetime

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.http import QueryDict
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.utils.timezone import make_aware

from myapp import stock_api
from myapp.models import *


# View for the home page - a list of 20 of the most active stocks
def index(request):
    notifications = ''
    number_of_notifs = 0
    favorite_stocks = []
    if request.user.is_authenticated:
        notifications = ReadyNotification.objects.filter(user=request.user).order_by('-id')
        number_of_notifs = len(notifications)
        notifications = notifications[:5]  # only recent 5
        user = request.user
        try:

            favorite_stocks = FavoriteStock.objects.get(user_id=request.user.id).stocks.all()

        except Exception as e:
            favorite_stocks = []

    data = Stock.objects.filter(top_rank__isnull=False).order_by('top_rank')
    return render(request, 'index.html', {
        'page_title': 'Main',
        'data': serializers.serialize('json', data),
        'notifications': notifications,
        'number_of_notifs': number_of_notifs,
        'favorite_stocks': serializers.serialize('json', favorite_stocks),
    })


def crypto(request):
    data = CryptoCurrency.objects.filter(rank__isnull=False).order_by('rank')
    data_json = serializers.serialize('json', data)
    return render(request, 'crypto.html', {'data': data_json})


def crypto_details(request, symbol='BTCUSD'):
    data = stock_api.crypto_details(symbol)
    return render(request, 'crypto_details.html', {
        'latestPrice': data['latestPrice'],
        'symbol': data['symbol'],
        'source': data['latestSource'],
        'latestUpdate': make_aware(datetime.fromtimestamp(data['latestUpdate'] / 1000)),
        'latestVolume': data['latestVolume']
    })


@login_required
def favorite_stock(request):
    user = request.user
    data = []
    try:
        data = FavoriteStock.objects.get(user_id=user.id).stocks.order_by('top_rank').all()
    except Exception:
        data = []
    return render(request, 'fav_stocks.html', {'page_title': 'Favorite Stokes', 'data': data})


def compare(request):
    return render(request, 'compare.html', {'stocks': request.GET.get('symbols')})


@login_required
def exchange(request):
    if not request.user.is_authenticated:
        return redirect(reverse('login'))
    user = request.user
    user_stocks = UserStock.objects.get(user_id=user.id)
    stocks = Stock.objects.filter(top_rank__isnull=False).order_by('top_rank')
    return render(request, 'exchange.html',
                  {'user_stocks': serializers.serialize('json', user_stocks.stock_buyied.all()),
                   'stocks': serializers.serialize('json', stocks),
                   'user_budget': user_stocks.budget})


# View for the single stock page
# symbol is the requested stock's symbol ('AAPL' for Apple)
def single_stock(request, symbol):
    try:
        data = stock_api.get_stock_info(symbol)
    except Exception:
        data = -1
    try:
        recs_data = stock_api.get_analyst_recommendations(symbol)
        rec = recs_data[0]
        try:
            rec['corporateActionsAppliedDate'] = datetime.fromtimestamp((
                    rec['corporateActionsAppliedDate'] / 1000.0)).strftime("%Y-%m-%d")
        except TypeError:
            rec['corporateActionsAppliedDate'] = "Unavailable"
    except Exception as e:
        rec = -1
    favorite = []
    if request.user.is_authenticated:
        try:
            favorite = FavoriteStock.objects.get(user_id=request.user.id).stocks.values_list('symbol', flat=True).all()
        except Exception as e:
            pass
    is_favorite = True if symbol in favorite else False
    return render(request, 'single_stock.html', {'page_title': 'Stock Page - %s' % symbol, 'data': data,
                                                 'rec': rec, 'is_favorite': is_favorite}, )


def portfolio(request):
    if not request.user.is_authenticated:
        return redirect(reverse('login'))
    user = request.user
    stocks = Stock.objects.filter(top_rank__isnull=False).order_by('top_rank')
    user_stocks = UserStock.objects.get(user_id=user.id)
    user_stocks_history = UserStockHistory.objects.get(user_id=user.id)
    return render(request, 'portfolio.html',
                  {'page_title': 'Portfolio',
                   'user_stocks': serializers.serialize('json', user_stocks.stock_buyied.all()),
                   'user_stocks_history': serializers.serialize('json',
                                                                user_stocks_history.stock_operation_history.all()),
                   'user_budget': user_stocks.budget,
                   'stocks': serializers.serialize('json', stocks)})


def register(request):
    # If post -> register the user and redirect to main page
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=email):
            error_message = f'user {email} already exist!'
            return render(request, 'register.html', {'page_title': 'Register', 'message': error_message})
        newuser = User.objects.create_user(username=email, email=email, password=password)
        newuser.first_name = firstname
        newuser.last_name = lastname
        newuser.save()
        user_stock = UserStock.objects.create(user=newuser)
        user_budget = float(request.POST.get('credit')) if request.POST.get('credit') else 0
        user_stock.budget = user_budget
        user_stock.save()
        user_stock_history = UserStockHistory.objects.create(user=newuser)
        user_stock_history.save()

        if request.FILES and request.POST.get('avatar') and request.FILES['avatar']:
            avatar = request.FILES['avatar']
            file_ext = pathlib.Path(avatar.name).suffix
            new_file_name = str(newuser.id) + file_ext
            user_profile = UserProfile(user=newuser, avatar=new_file_name)
            fs = FileSystemStorage()
            fs.save(new_file_name, avatar)
            user_profile.save()

        return redirect('index')
    else:
        # If not post (regular request) -> render register page
        return render(request, 'register.html', {'page_title': 'Register'})


def user_profile(request):
    if request.user.is_authenticated:
        user = request.user
        profile = UserProfile.objects.filter(user_id=user.id)
        avatar = 'default.png'
        if profile:
            avatar = profile[0].avatar
        return render(request, 'profile.html',
                      {'page_title': 'User Profile', 'user': user, 'media_url': settings.MEDIA_URL, 'avatar': avatar})
    return render(request, 'register.html', {'page_title': 'Register'})


def buy_stock(request):
    if not request.user.is_authenticated:
        return render(request, 'register.html', {'page_title': 'Register'})
    user = request.user
    user_stock_info = UserStock.objects.get(user_id=user.id)
    user_stock_history = UserStockHistory.objects.get(user_id=user.id)

    request_body = QueryDict(request.body)
    if not request_body.get('symbol') or not request_body.get('stock_number'):
        return JsonResponse({"error": "wrong data"})

    stock_symbol = request_body.get('symbol')
    stock_number = float(request_body.get('stock_number'))
    stock = Stock.objects.get(symbol=stock_symbol)
    stock_cost = stock_number * float(stock.price)
    if request.method == 'POST':
        if (user_stock_info.budget < stock_cost):
            return JsonResponse({"error": "no enough budget"})
        if not user_stock_info.stock_buyied:
            user_stock_info.user_stock_info = []
            user_stock_info.save()
        user_stock = user_stock_info.stock_buyied.all().filter(
            stock_id=stock_symbol)
        if user_stock:
            old_stock_cost = float(user_stock[0].stock_number) * float(user_stock[0].stock_price)
            new_stock_cost = stock_number * stock.price
            total_stock_cost = old_stock_cost + new_stock_cost
            total_number = float(user_stock[0].stock_number) + stock_number
            user_stock[0].stock_number = total_number
            user_stock[0].stock_price = total_stock_cost / total_number
            user_stock[0].save()
        else:
            new_stock = StockOperation.objects.create(
                stock=stock, stock_number=stock_number, stock_price=float(stock.price))
            new_stock.save()
            user_stock_info.stock_buyied.add(new_stock)

        user_stock_info.budget = float(user_stock_info.budget) - stock_cost
        user_stock_info.save()
        # add to history
        stock_history = StockOperationHistory.objects.create(
            stock=stock, stock_number=stock_number, stock_price=float(stock.price), stock_operation=True)
        stock_history.save()
        user_stock_history.stock_operation_history.add(stock_history)
        user_stock_history.save()
        return JsonResponse({'user_budget': user_stock_info.budget})

    if request.method == 'DELETE':
        user_stock = user_stock_info.stock_buyied.all().get(
            stock_id=stock_symbol)
        if float(user_stock.stock_number) < stock_number:
            return JsonResponse({"error": "no enough stock to buy"})
        user_stock.stock_number = float(user_stock.stock_number) - stock_number
        if user_stock.stock_number == 0:
            user_stock_info.stock_buyied.remove(user_stock)
            user_stock.delete()
        else:
            user_stock.save()

        user_stock_info.budget = float(user_stock_info.budget) + stock_cost
        user_stock_info.save()
        # add to history
        stock_history = StockOperationHistory.objects.create(
            stock=stock, stock_number=stock_number, stock_price=float(stock.price), stock_operation=False)
        stock_history.save()
        user_stock_history.stock_operation_history.add(stock_history)
        user_stock_history.save()
        return JsonResponse({'user_budget': user_stock_info.budget})


def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('re_firstname') or user.first_name
        user.last_name = request.POST.get('re_lastname') or user.last_name
        password = request.POST.get('re_password')
        if password:
            user.set_password(password)

        user.save()
        if request.FILES and request.POST.get('avatar') and request.FILES.get('avatar'):
            avatar = request.FILES['avatar']
            fs = FileSystemStorage()
            file_ext = pathlib.Path(avatar.name).suffix
            new_file_name = str(user.id) + file_ext
            try:
                user_profile = UserProfile.objects.get(user_id=user.id)
                fs.delete(user_profile.avatar)
                user_profile.avatar = new_file_name

            except Exception:
                user_profile = UserProfile(user=user, avatar=new_file_name)
            fs.save(new_file_name, avatar)
            user_profile.save()
        return redirect('index')
    else:
        # If not post (regular request) -> render register page
        return render(request, 'edit_profile.html', {'page_title': 'Edit Profile'})


def change_password(request):
    if request.method == 'POST' and request.user.is_authenticated:
        user = request.user
        password = request.POST.get('password')
        user.set_password(password)
        user.save()
        return redirect('index')
    else:
        # If not post (regular request) -> render register page
        return render(request, 'register.html', {'page_title': 'Register'})


def logout_view(request):
    logout(request)
    return redirect('index')


# API for a stock's price over time
# symbol is the requested stock's symbol ('AAPL' for Apple)
# The response is JSON data of an array composed of "snapshot" objects (date + stock info + ...), usually one per day
def single_stock_historic(request, symbol, time_range='1m'):
    data = stock_api.get_stock_historic_prices(symbol, time_range=time_range)
    return JsonResponse({'data': data})


def get_company_desc(request, company_symbol):
    try:
        comp = Company.objects.get(company_symbol=company_symbol)
        return JsonResponse({'summary': comp.company_desc})
    except Exception as e:
        print(e)
        return JsonResponse({'summary': 'Couldn\'t find information'})


def multi_stocks_historic(request, stocks, time_range='1m'):
    result = []
    stocks_list = stocks.split('-')

    for stock in stocks_list:
        result.append({'name': stock, 'data': stock_api.get_stock_historic_prices(stock, time_range=time_range)})

    return JsonResponse({'data': result}, content_type="application/json")


def stocks_names_and_symbols(request):
    data = Stock.objects.filter(top_rank__isnull=False).order_by('name')
    result = []
    for datum in data:
        result.append('{} - {}'.format(datum.symbol, datum.name))
    return JsonResponse({'data': result}, content_type="application/json")


@login_required
def my_notifications(request):
    waiting_notifs = Notification.objects.filter(user=request.user)
    active_notifs = ReadyNotification.objects.filter(user=request.user)
    analyst_notifs = NotificationAnalystRec.objects.filter(user=request.user)
    tracking_notifs = TrackStock.objects.filter(user=request.user)

    context = {
        'waiting_notifs': waiting_notifs,
        'active_notifs': active_notifs,
        'analyst_notifs': analyst_notifs,
        'tracking_notifs': tracking_notifs,
    }
    return render(request, 'my_notifications.html', context)


@login_required
def delete_active_notification(request, pk='-1'):
    if request.user.is_authenticated:
        if pk != '-1':
            n = ReadyNotification.objects.filter(user=request.user, id=pk)
            if n:
                n.delete()

    return redirect('my_notifications')


@login_required
def delete_waiting_notification(request, pk='-1'):
    if request.user.is_authenticated:
        if pk != '-1':
            n = Notification.objects.filter(user=request.user, id=pk)
            if n:
                n.delete()

    return redirect('my_notifications')


@login_required
def delete_tracking_notification(request, pk='-1'):
    if request.user.is_authenticated:
        if pk != '-1':
            n = TrackStock.objects.filter(user=request.user, id=pk)
            if n:
                n.delete()

    return redirect('my_notifications')


@login_required
def delete_analyst_notification(request, pk='-1'):
    if request.user.is_authenticated:
        if pk != '-1':
            n = NotificationAnalystRec.objects.filter(user=request.user, id=pk)
            if n:
                n.delete()

    return redirect('my_notifications')

# def get_top_five_notifs(request):
#     number_of_notifs = 0
#     notifications = []
#     if request.user.is_authenticated:
#         notifications = ReadyNotification.objects.filter(user=request.user).values('company_symbol',
#                                                                                    'description',
#                                                                                    'time').order_by('-id')
#         number_of_notifs = len(notifications)
#         notifications = notifications[:5]  # only recent 5
#     return JsonResponse(
#         {'number_of_notifs': number_of_notifs, 'notifications':     notifications},
#         content_type="application/json")
