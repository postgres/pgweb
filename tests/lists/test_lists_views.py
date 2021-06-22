from django.test import TestCase, Client
import json


class TestListsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testListsViewIsResolved(self):
        response = self.client.get('/community/lists/listinfo', {}, True)
        self.assertEquals(response.status_code, 200)
