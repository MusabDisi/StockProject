from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.events import EVENT_ALL
from .models import Notification, ReadyNotification, TrackStock, NotificationAnalystRec
from django.utils.timezone import now
from myapp import stock_api
import datetime
from dateutil.relativedelta import relativedelta, FR
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# When we already have a job running what to do? we can use max_instances keyword
# this class uses apsscheduler
# further info can be found at https://apscheduler.readthedocs.io/en/stable/userguide.html
def send_to_socket(user, company_symbol, description, time):
    channel_layer = get_channel_layer()
    data_to_socket = {
        "symbol": company_symbol,
        "description": description,
        "time": time,
    }

    # Trigger message sent to group
    async_to_sync(channel_layer.group_send)(
        str(user.pk),  # Group Name, Should always be string
        {
            "type": "notify",  # custom function in consumer.py
            "data": data_to_socket,
        },  # message
    )


class NotificationsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notifications_id = 'notifications_job'
        self.stock_tracking_id = 'tracking_job'
        self.analyst_rec_id = 'analyst_rec_job'

    def start(self):
        print('Started running the jobs')
        self.scheduler.add_job(self.set_active_notifications, 'interval', seconds=30, id=self.notifications_id)
        self.scheduler.add_job(self.check_tracking_model, 'interval', hours=12, id=self.stock_tracking_id)
        self.scheduler.add_job(self.check_notifications_analyst, 'interval', days=1, id=self.analyst_rec_id)

        # self.scheduler.add_listener(self.job_listener, EVENT_ALL)
        self.scheduler.start()

    def stop(self, job_id):
        self.scheduler.remove_job(job_id)

    def pause(self, job_id):
        self.scheduler.pause_job(job_id)

    def resume(self, job_id):
        self.scheduler.resume_job(job_id)

    @staticmethod
    def get_value_of(symbol, operand):
        cached = cache.get(symbol + operand)  # ex: AAPLHigh or None
        if cached:
            print('cached')
            return cached
        else:
            data = stock_api.get_stock_info_notification(symbol, operand)
            cache.set(symbol + operand, data, (30 * 60))  # cache for 30 mins
            return data

    @staticmethod
    def get_analyst_record_of(symbol):
        cached = cache.get(symbol + 'analystRec')
        if cached:
            print('cached')
            return cached
        else:
            data = stock_api.get_analyst_recommendations(symbol)
            if data:
                rec = data[0]
                rec = rec.get('ratingScaleMark')
                cache.set(symbol + 'analystRec', rec, (30 * 60))  # cache for 30 mins
                return rec
            else:
                return 0

    @staticmethod
    def is_bigger(value, api_value):
        return api_value > value

    @staticmethod
    def is_lower(value, api_value):
        return api_value < value

    @staticmethod
    def is_equal(value, api_value):
        return api_value == value

    # loops over Notification table and check if any notification must be triggered
    # if yes add it to ReadyNotification table
    def set_active_notifications(self):
        notifications = Notification.objects.all()
        operators = {'bigger': self.is_bigger, 'lower': self.is_lower, 'equal': self.is_equal}
        for notification in notifications:
            time_now = now()
            should_check = (((time_now - notification.last_checked).seconds // 60 % 60) >= 0)  # check if 0 mins passed
            if should_check:
                user = notification.user
                key = notification.operand
                symbol = notification.company_symbol
                api_value = self.get_value_of(symbol, key)
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
                    send_to_socket(user, rn.company_symbol, rn.description, str(rn.time.replace(microsecond=0)))
                else:
                    notification.last_checked = now()
                    notification.save()

    def cut_data(self, data, creation_time):
        today = str((now() + relativedelta(weekday=FR(-1))).date())
        creation_time = str(creation_time)
        idx1 = 0
        idx2 = 0
        for idx, i in enumerate(data):
            if i['date'] == creation_time:
                idx1 = idx
            if i['date'] == today:
                idx2 = idx
        return data[idx1:idx2]

    def is_increasing(self, data, operand):
        temp = 0
        for i in data:
            value = i[operand]
            print('value', value)
            if value < temp:
                return False
            else:
                temp = value
        return True

    def is_decreasing(self, data, operand):
        temp = 0
        for i in data:
            value = i[operand]
            if value > temp:
                return False
            else:
                temp = value
        return True

    def should_trigger(self, operand, state, symbol, weeks, creation_time):
        if operand == 1:
            operand = 'high'
        elif operand == -1:
            operand = 'low'
        else:
            return False
        if weeks < 4:
            time_range = '1m'
        elif weeks < 8:
            time_range = '3m'
        else:
            time_range = '6m'

        data = stock_api.get_stock_historic_prices(symbol, time_range, 'date,' + operand)
        data = self.cut_data(data, creation_time)
        if not data:
            return False
        else:
            if state == 1:
                return self.is_increasing(data, operand)
            else:
                return self.is_decreasing(data, operand)

    def check_tracking_model(self):
        today = datetime.datetime.today().weekday()
        if not (today == 6):  # if today is not Saturday or Sunday
            return  # Don't check
        tracking = TrackStock.objects.all()
        for track in tracking:
            creation_time = track.creation_time
            weeks = track.weeks
            date_now = now().date()
            should_check = ((date_now - creation_time).days >= ((weeks * 7) - (weeks * 2)))
            if should_check:
                user = track.user
                operand = track.operand
                state = track.state
                company_symbol = track.company_symbol
                should_trigger = self.should_trigger(operand, state, company_symbol, weeks, creation_time)
                if should_trigger:
                    if operand == 1:
                        operand = 'High'
                    else:
                        operand = 'Low'
                    if state == 1:
                        description = operand + ' kept increasing for the last ' + str(weeks) + ' week/s.'
                    else:
                        description = operand + ' kept decreasing for the last ' + str(weeks) + ' week/s.'
                    rn = ReadyNotification(user=user, description=description, company_symbol=company_symbol)
                    rn.save()
                    track.delete()
                    send_to_socket(user, rn.company_symbol, rn.description, str(rn.time))
                else:
                    if operand == 1:
                        operand = 'High'
                    else:
                        operand = 'Low'
                    if state == 1:
                        description = operand + ' didn\'t keep increasing for the last ' + str(weeks) + ' week/s.'
                    else:
                        description = operand + ' didn\'t keep decreasing for the last ' + str(weeks) + ' week/s.'
                    rn = ReadyNotification(user=user, description=description, company_symbol=company_symbol)
                    rn.save()
                    track.delete()
                    send_to_socket(user, rn.company_symbol, rn.description, str(rn.time))

    def check_notifications_analyst(self):
        notifications = NotificationAnalystRec.objects.all()
        operators = {'bigger': self.is_bigger, 'lower': self.is_lower, 'equal': self.is_equal}
        for notification in notifications:
            time_now = now()
            should_check = (((time_now - notification.last_checked).seconds // 60 % 60) >= 0)  # check if 10 mins passed
            if should_check:
                user = notification.user
                symbol = notification.company_symbol
                api_value = self.get_analyst_record_of(symbol)
                operator = notification.operator
                value = notification.value
                should_activate = operators[operator](value, api_value)
                if should_activate:
                    description = 'Analyst Scale Rate ' + str(operator) + ' than ' + str(value)
                    rn = ReadyNotification(user=user, description=description, company_symbol=symbol)
                    rn.save()
                    notification.delete()
                    send_to_socket(user, rn.company_symbol, rn.description, str(rn.time))
                else:
                    notification.last_checked = now()
                    notification.save()
