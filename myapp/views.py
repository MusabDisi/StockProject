from django.shortcuts import render, redirect, HttpResponse
from myapp import stock_api
from django.core.paginator import Paginator
from django.conf import settings
from myapp.models import Stock, UserProfile, Notification, ReadyNotification, Company
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout
import wikipedia as wiki
from django.core.files.storage import FileSystemStorage
import pathlib
from django.utils.timezone import now
from asgiref.sync import sync_to_async


# View for the home page - a list of 20 of the most active stocks
def index(request, page='1'):
    # Query the stock table, filter for top ranked stocks and order by their rank.
    print('...... index called')
    notifications = ''
    if request.user.is_authenticated:
        set_active_notifications(request.user)
        notifications = ReadyNotification.objects.filter(user=request.user).order_by('-id')[:5]  # only recent 5
        # notifications = ReadyNotification.objects.filter(user=request.user)

    if request.method == 'GET':
        page = request.GET.get('page')

    try:  # in case user inters un valid page go to main
        if page is not None:
            int(page)
        else:
            page = '1'
    except ValueError:
        page = '1'

    data = Stock.objects.filter(top_rank__isnull=False).order_by('top_rank')

    paginator = Paginator(data, 11)

    data = paginator.get_page(page)

    to_add = (11 * (int(page) - 1))  # used for numbering the stocks in the list

    return render(request, 'index.html', {'page_title': 'Main', 'data': data, 'to_add': to_add,
                                          'notifications': notifications})


def get_value_of(symbol, operand):
    return stock_api.get_stock_info_notification(symbol, operand)


def is_bigger(value, api_value):
    return api_value > value


def is_lower(value, api_value):
    return api_value < value


def is_equal(value, api_value):
    return api_value == value


# loops over Notification table and check if any notification must be triggered
# if yes add it to ReadyNotification table
def set_active_notifications(user):
    notifications = Notification.objects.filter(user=user)
    operators = {'bigger': is_bigger, 'lower': is_lower, 'equal': is_equal}
    for notification in notifications:
        time_now = now()
        should_check = (((time_now - notification.last_checked).seconds // 60 % 60) >= 0)  # check if 10 mins passed
        if should_check:
            key = notification.operand
            symbol = notification.company_symbol
            api_value = get_value_of(symbol, key)
            operator = notification.operator
            value = notification.value
            if api_value[key] is None:
                api_value = 0
            else:
                api_value = api_value[key]
            should_activate = operators[operator](value, api_value)
            if should_activate:
                description = key + ' is ' + operator + ' than ' + str(value)
                rn = ReadyNotification(user=user, description=description, company_symbol=symbol)
                rn.save()
                notification.delete()


# View for the single stock page
# symbol is the requested stock's symbol ('AAPL' for Apple)
def single_stock(request, symbol):
    data = stock_api.get_stock_info(symbol)
    # high = check_if_notification_set(request.user, symbol, 'high')
    # low = check_if_notification_set(request.user, symbol, 'low')
    return render(request, 'single_stock.html', {'page_title': 'Stock Page - %s' % symbol, 'data': data})


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

# call wikipedia api
# def get_wiki_info(request, company_name):
#     try:
#         summary = wiki.summary(company_name, sentences=3)
#         return JsonResponse({'summary': summary})
#     except Exception:
#         return JsonResponse({'summary': "Couldn't find information"})


def get_company_desc(request, company_symbol):
    try:
        comp = Company.objects.get(company_symbol=company_symbol)
        return JsonResponse({'summary': comp.company_desc})
    except Exception as e:
        print(e)
        return JsonResponse({'summary': "Couldn't find information"})

def add_notification(request):
    print('received')
    if request.method == "POST":
        print('posting', request.POST)
        if request.user.is_authenticated:
            for i in range(20):
                notification = Notification(user=request.user, operator=request.POST.get('operator').strip()
                                            , operand=request.POST.get('operand').strip()
                                            , value=request.POST.get('value').strip()
                                            , company_symbol=request.POST.get('company_symbol').strip())
                notification.save()
    return HttpResponse(status=204)


def my_notifications(request):
    waiting_notifs = Notification.objects.filter(user=request.user)
    active_notifs = ReadyNotification.objects.filter(user=request.user)
    context = {
        'waiting_notifs': waiting_notifs,
        'active_notifs': active_notifs,
    }
    return render(request, 'my_notifications.html', context)


def delete_active_notification(request, pk='-1'):
    print('delete active')
    if request.user.is_authenticated:
        if pk != '-1':
            n = ReadyNotification.objects.filter(user=request.user, id=pk)
            if n:
                n.delete()

    return redirect('my_notifications')


def delete_waiting_notification(request, pk='-1'):
    if request.user.is_authenticated:
        if pk != '-1':
            n = Notification.objects.filter(user=request.user, id=pk)
            if n:
                n.delete()

    return redirect('my_notifications')
