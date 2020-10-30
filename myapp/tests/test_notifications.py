from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse
from myapp.views import *
import json
from myapp.models import Company


class TestNotifications(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        test_password = 'secret'
        self.user = User.objects.create_user(username='TestName', email='test@test.com', password=test_password)
        self.company = Company.objects.create(sector_name='sector', company_name='name',
                                              company_symbol='symbol', company_desc='desc')
        self.client.login(username=self.user.username, password=test_password)

    def test_get_company_desc(self):
        url = reverse('get_company_description', args=['symbol'])

        request = self.factory.get(url)
        request.user = self.user

        response = get_company_desc(request, 'symbol')
        response_content_json = json.loads(response.content)

        self.assertEqual(response_content_json, {'summary': 'desc'})

    def test_get_company_desc_fail(self):  # company doesn't exist
        url = reverse('get_company_description', args=['symbol'])

        request = self.factory.get(url)
        request.user = self.user

        response = get_company_desc(request, 'symbol_fake')
        response_content_json = json.loads(response.content)

        self.assertEqual(response_content_json, {'summary': 'Couldn\'t find information'})

    def test_add_notification_OK(self):
        url = reverse('notification')

        data = {'user': self.user, 'operand': 'High',
                'value': '50', 'company_symbol': 'symbol', 'operator': '>'}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 204)  # 204 => Ok No content

    def test_add_notification_analyst(self):
        url = reverse('notification-analyst')

        data = {'user': self.user, 'operator': 'operator',
                'value': '50', 'company_symbol': 'symbol'}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 204)  # 204 => Ok No content

    def test_add_tracking(self):
        url = reverse('add_tracking')

        data = {'operand': 1, 'state': 50, 'company_symbol': 'symbol',
                'weeks': 2, 'creation_time': datetime.date(2120, 12, 31)}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 204)  # 204 => Ok No content

    def test_my_notifications(self):
        url = reverse('my_notifications')

        response = self.client.get(url)  # used client so we can check template used

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_notifications.html')

    def test_delete_active_notification(self):
        # create fake notification
        fake_notif = ReadyNotification.objects.create(user=self.user, company_symbol='symbol',
                                                      description='desc')

        request_url = reverse('delete_active_notification', args=[fake_notif.id])
        redirect_url = reverse('my_notifications')

        response = self.client.get(request_url)  # send delete request

        self.assertEqual(ReadyNotification.objects.filter(id=fake_notif.id).count(), 0)  # was deleted
        self.assertEqual(response.status_code, 302)  # 302 => redirect
        self.assertRedirects(response, redirect_url)

    def test_delete_waiting_notification(self):
        # create fake notification
        fake_notif = Notification.objects.create(user=self.user, company_symbol='symbol',
                                                 operand='operand', operator='operator',
                                                 value=20)

        request_url = reverse('delete_waiting_notification', args=[fake_notif.id])
        redirect_url = reverse('my_notifications')

        response = self.client.get(request_url)  # send delete request

        self.assertEqual(Notification.objects.filter(id=fake_notif.id).count(), 0)  # was deleted
        self.assertEqual(response.status_code, 302)  # 302 => redirect
        self.assertRedirects(response, redirect_url)  # redirected to correct url

    def test_delete_tracking_notification(self):
        # create fake notification
        fake_notif = TrackStock.objects.create(user=self.user, company_symbol='symbol',
                                               operand=1, state=1,
                                               weeks=20, creation_time=datetime.date(2120, 12, 31))

        request_url = reverse('delete_tracking_notification', args=[fake_notif.id])
        redirect_url = reverse('my_notifications')

        response = self.client.get(request_url)  # send delete request

        self.assertEqual(TrackStock.objects.filter(id=fake_notif.id).count(), 0)  # was deleted
        self.assertEqual(response.status_code, 302)  # 302 => redirect
        self.assertRedirects(response, redirect_url)  # redirected to correct url

    def test_delete_analyst_notification(self):
        # create fake notification
        fake_notif = NotificationAnalystRec.objects.create(user=self.user, company_symbol='symbol',
                                                           operator='>', value=20)

        request_url = reverse('delete_analyst_notification', args=[fake_notif.id])
        redirect_url = reverse('my_notifications')

        response = self.client.get(request_url)  # send delete request

        self.assertEqual(NotificationAnalystRec.objects.filter(id=fake_notif.id).count(), 0)  # was deleted
        self.assertEqual(response.status_code, 302)  # 302 => redirect
        self.assertRedirects(response, redirect_url)  # redirected to correct url
