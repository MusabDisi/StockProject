from django.shortcuts import render, redirect
from myapp import stock_api
from myapp.models import Stock
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout
import wikipedia as wiki
from django.core.paginator import Paginator


# View for the home page - a list of 20 of the most active stocks
def index(request, page='1'):
    # Query the stock table, filter for top ranked stocks and order by their rank.

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

    return render(request, 'index.html', {'page_title': 'Main', 'data': data, 'to_add': to_add})


# View for the single stock page
# symbol is the requested stock's symbol ('AAPL' for Apple)
def single_stock(request, symbol):
    data = stock_api.get_stock_info(symbol)
    return render(request, 'single_stock.html', {'page_title': 'Stock Page - %s' % symbol, 'data': data})


def register(request):
    # If post -> register the user and redirect to main page
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('password')

        newuser = User.objects.create_user(username=email, email=email, password=password)
        newuser.first_name = firstname
        newuser.last_name = lastname
        newuser.save()
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


def get_wiki_info(request, company_name):
    try:
        summary = wiki.summary(company_name, sentences=3)
        return JsonResponse({'summary': summary})
    except Exception:
        return JsonResponse({'summary': "Couldn't find information"})
