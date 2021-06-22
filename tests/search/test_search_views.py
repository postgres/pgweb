from django.test import TestCase, Client


class TestSearchViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testSearchViewIsResolved(self):
        response = self.client.get('/search/', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/sitesearch.html')
