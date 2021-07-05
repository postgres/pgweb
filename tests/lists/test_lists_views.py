from django.test import TestCase, Client
import json


class TestListsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_lists_view_is_resolved(self):
        response = self.client.get('/community/lists/listinfo', {}, True)
        self.assertEquals(response.status_code, 200)
