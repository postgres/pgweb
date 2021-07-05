from django.test import TestCase, Client


class TestNewsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_news_view_is_resolved(self):
        response = self.client.get('/about/newsarchive', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/newsarchive.html')
