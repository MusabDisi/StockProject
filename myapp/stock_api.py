import requests

# Sandbox API - FOR TESTING
BASE_URL_SANDBOX = 'https://sandbox.iexapis.com'
PUBLIC_TOKEN_SANDBOX = 'Tpk_31522a5f3a3f40c5a08af821908adf96'

# Real API - FOR PRODUCTION
# YOU NEED TO CREATE AN ACCOUNT TO RECEIVE YOUR OWN API KEYS (its free)
BASE_URL = 'https://cloud.iexapis.com'
PUBLIC_TOKEN = 'pk_5169755953b14b5d98b0ba75724327a4'


# For general info for all symbols
# https://cloud.iexapis.com/stable/re
# f-data/symbols?token=pk_dd07f5a1aaea4a039cfe8118f3d9727a


# For all symbols with prices (*free weight*)
# https://cloud.iexapis.com/stable/tops/last?token=pk_dd07f5a1aaea4a039cfe8118f3d9727a
def _request_data(url, filter='', additional_parameters={}):
    print("requested real data from api")
    final_url = BASE_URL + url

    query_strings = {
        'token': PUBLIC_TOKEN
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
    print(response.json())
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
    # 'symbol,companyName,marketcap,totalCash,primaryExchange,latestPrice,latestSource,change,changePercent'
    return _request_data_sandbox('/stable/stock/{symbol}/quote'.format(symbol=symbol),
                                 additional_parameters={'displayPercent': 'true'})


def get_stock_historic_prices(symbol, time_range='1m'):
    return _request_data_sandbox('/stable/stock/{symbol}/chart/{time_range}'
                                 .format(symbol=symbol, time_range=time_range))
