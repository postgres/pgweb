from django.test import TestCase, Client


class TestCoreViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testHomeViewIsResolved(self):
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
