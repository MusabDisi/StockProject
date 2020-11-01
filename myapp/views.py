from django.shortcuts import render, redirect
from myapp import stock_api
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings
from django.http import QueryDict
from django.urls import reverse
from myapp.models import Stock, UserProfile, UserStock, StockOperation, FavoriteStock
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import logout
from django.core import serializers
# import wikipedia as wiki
from django.core.files.storage import FileSystemStorage
import pathlib
from dateutil.relativedelta import relativedelta, MO
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from myapp import stock_api
from myapp.models import *

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_202_ACCEPTED = 202
HTTP_204_NO_CONTENT = 204
HTTP_304_NOT_MODIFIED = 304
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_500_INTERNAL_SERVER_ERROR = 500



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
          favorite_stocks = FavoriteStock.objects.get(user_id = request.user.id).stocks.all()
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

def favorite_stock(request):
	user = request.user
	data = FavoriteStock.objects.get(user_id = user.id).stocks.order_by('top_rank').all()
	return render(request, 'fav_stocks.html', {'page_title': 'Favorite Stokes', 'data': data })

def compare(request):
    return render(request, 'compare.html', {'stocks': request.GET.get('symbols')})

def exchange(request):
	if not request.user.is_authenticated:
		return redirect(reverse('login'))
	user = request.user
	user_stocks = UserStock.objects.get(user_id=user.id)
	stocks = Stock.objects.all()
	return render(request, 'exchange.html', {'user_stocks': user_stocks.stock_buyied.all(), 'stocks': stocks, 'user_budget': user_stocks.budget})

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
            rec['corporateActionsAppliedDate'] = datetime.datetime.fromtimestamp((
                    rec['corporateActionsAppliedDate'] / 1000.0)).strftime("%Y-%m-%d")
        except TypeError:
            rec['corporateActionsAppliedDate'] = "Unavailable"
    except Exception:
        rec = -1
    favorite = []
    if request.user.is_authenticated:
        try:
            favorite = FavoriteStock.objects.get(user_id = request.user.id).stocks.values_list('symbol', flat=True).all()
        except Exception as e:
            favorite = False
    is_favorite = True if symbol in favorite else False
    return render(request, 'single_stock.html', {'page_title': 'Stock Page - %s' % symbol, 'data': data,
                                                 'rec': rec, 'is_favorite': is_favorite}, )


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
            user_stock[0].stock_number = float(
                user_stock[0].stock_number) + stock_number
            user_stock[0].save()
        else:
            new_stock = StockOperation.objects.create(
                stock=stock, stock_number=stock_number)
            new_stock.save()
            user_stock_info.stock_buyied.add(new_stock)
        user_stock_info.budget = float(user_stock_info.budget) - stock_cost
        user_stock_info.save()
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


@login_required
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


def add_notification(request):
    print('received')
    if request.method == "POST":
        print('posting', request.POST)
        if request.user.is_authenticated:
            notification = Notification(user=request.user, operator=request.POST.get('operator').strip()
                                        , operand=request.POST.get('operand').strip()
                                        , value=request.POST.get('value').strip()
                                        , company_symbol=request.POST.get('company_symbol').strip())

            notification.save()

    return HttpResponse(status=HTTP_204_NO_CONTENT)


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


# TODO: make datetime zone aware
def get_time(include_this_week):
    # Mon 0 - Sun 6
    today = datetime.datetime.now().weekday()
    if today == 0:  # if today is Monday return the date
        return now().date()

    if include_this_week == '1':
        if today == 5:  # if today is Saturday
            return (now() + relativedelta(weekday=MO(+1))).date()  # return date of next Monday
        elif today == 6:  # if today is Sunday
            return (now() + relativedelta(weekday=MO(+1))).date()  # return date of next Monday
        else:
            return (now() + relativedelta(weekday=MO(-1))).date()  # return date of prev Monday
    else:  # go to next week
        return (now() + relativedelta(weekday=MO(+1))).date()  # return date of next Monday


# TODO: show feedback to user
@login_required
def add_tracking(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            post = request.POST
            track = TrackStock(user=request.user, operand=int(post.get('operand')), state=int(post.get('state'))
                               , weeks=int(post.get('weeks')), company_symbol=post.get('company_symbol'),
                               creation_time=get_time(post.get('include_this_week')))
            track.save()

    return HttpResponse(status=HTTP_204_NO_CONTENT)


@login_required
def add_notification_analyst(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            post = request.POST
            notif = NotificationAnalystRec(user=request.user, operator=post.get('operator').strip()
                                           , value=post.get('value').strip()
                                           , company_symbol=post.get('company_symbol').strip())
            notif.save()

    return HttpResponse(status=HTTP_204_NO_CONTENT)


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
