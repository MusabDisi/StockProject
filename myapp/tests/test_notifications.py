from unittest import TestCase
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse
from myapp.views import get_company_desc
import json
from myapp.models import Company


class TestNotifications(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User(username='TestName', email='test@test.com', password='shh')
        self.company = Company(sector_name='sector', company_name='name',
                               company_symbol='symbol', company_desc='desc')

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

    def test_add_notification(self):
        pass