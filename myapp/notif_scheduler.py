from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_ALL
from .models import Notification, ReadyNotification, TrackStock
from django.utils.timezone import now
from myapp import stock_api
import datetime
from dateutil.relativedelta import relativedelta, FR


# TODO: When we already have a job running what to do?
# TODO: Caching system
# TODO: Event listener for exceptions
# this class uses apsscheduler
# further info can be found at https://apscheduler.readthedocs.io/en/stable/userguide.html
class NotificationsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notifications_id = 'notifications_job'
        self.stock_tracking_id = 'tracking_job'

    def start(self):
        print('Started running the job')
        self.scheduler.add_job(self.set_active_notifications, 'interval', hours=1, id=self.notifications_id)
        self.scheduler.add_job(self.check_tracking_model, 'interval', hours=12, id=self.stock_tracking_id)

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
        return stock_api.get_stock_info_notification(symbol, operand)

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
            should_check = (((time_now - notification.last_checked).seconds // 60 % 60) >= 0)  # check if 10 mins passed
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

    # def job_listener(self, event):
    #     if event.exception:
    #         print('The job crashed :(')
    #         raise event.exception
    #     else:
    #         print('The job worked :)')
