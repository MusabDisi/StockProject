from dateutil.relativedelta import relativedelta, MO
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse
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
