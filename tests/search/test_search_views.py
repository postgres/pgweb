from django.test import TestCase, Client


class TestSearchViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_view_is_resolved(self):
        response = self.client.get('/search/', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/sitesearch.html')
