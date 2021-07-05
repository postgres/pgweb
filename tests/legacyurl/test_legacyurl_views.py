from django.test import TestCase, Client


class TestLegacyURLSViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_mail_pref_URL_is_redirected(self):
        response = self.client.get('/mailpref/abc')
        self.assertEquals(response.status_code, 301)
