import requests

# Sandbox API - FOR TESTING
BASE_URL_SANDBOX = 'https://sandbox.iexapis.com'
PUBLIC_TOKEN_SANDBOX = 'Tpk_31522a5f3a3f40c5a08af821908adf96'


# Real API - FOR PRODUCTION
# BASE_URL = 'https://cloud.iexapis.com'
# PUBLIC_TOKEN = 'pk_5169755953b14b5d98b0ba75724327a4'


# For general info for all symbols
# https://cloud.iexapis.com/stable/re
# f-data/symbols?token=pk_dd07f5a1aaea4a039cfe8118f3d9727a


# For all symbols with prices (*free weight*)
# https://cloud.iexapis.com/stable/tops/last?token=pk_dd07f5a1aaea4a039cfe8118f3d9727a
def _request_data(url, filter='', additional_parameters={}):
    # print("requested real data from api")
    final_url = BASE_URL_SANDBOX + url

    query_strings = {
        'token': PUBLIC_TOKEN_SANDBOX
    }
    query_strings.update(additional_parameters)

    if filter:
        query_strings['filter'] = filter

    response = requests.get(final_url, params=query_strings)

    if not response.ok:
        raise Exception('Unexpected response: ', response.__dict__)
    return response.json()


def _request_data_sandbox(url, filter='', additional_parameters={}):
    print("requested from sandbox")
    final_url = BASE_URL_SANDBOX + url

    query_strings = {
        'token': PUBLIC_TOKEN_SANDBOX,
    }
    query_strings.update(additional_parameters)

    if filter:
        query_strings['filter'] = filter

    response = requests.get(final_url, params=query_strings)
    if not response.ok:
        raise Exception('Unexpected response: ', response.__dict__)
    return response.json()


def _get_top_stocks():
    return _request_data('/stable/stock/market/list/mostactive',
                         filter='symbol,companyName,latestVolume,change,changePercent,primaryExchange,marketCap,'
                                'latestPrice,calculationPrice',
                         additional_parameters={'displayPercent': 'true', 'listLimit': '100000'})


# def _get_all_stocks():
#     return _request_data('/stable/stock/market/list/mostactive',
#                          filter='symbol,companyName,latestVolume,change,changePercent,primaryExchange,marketCap,'
#                                 'latestPrice,calculationPrice',
#                          additional_parameters={'displayPercent': 'true', 'listLimit': '40'})
#


def get_stock_info(symbol):
    # 'symbol,companyName,marketCap,totalCash,primaryExchange,latestPrice,latestSource,change,changePercent'
    return _request_data_sandbox('/stable/stock/{symbol}/quote'.format(symbol=symbol),
                                 additional_parameters={'displayPercent': 'true'})


# Range must be in ['max', '5y', '2y', '1y', 'ytd', '6m', '3m',
#                  '1m', '1mm', '5d', '5dm', '1d', 'dynamic']
# more info at https://iexcloud.io/docs/api/#historical-prices
def get_stock_historic_prices(symbol, time_range='1m', filter=''):
    return _request_data_sandbox('/stable/stock/{symbol}/chart/{time_range}'
                                 .format(symbol=symbol, time_range=time_range),
                                 filter=filter)


def get_stock_info_notification(symbol, operand):
    return _request_data_sandbox('/stable/stock/{symbol}/quote'.format(symbol=symbol),
                                 additional_parameters={'displayPercent': 'true'},
                                 filter=operand)
