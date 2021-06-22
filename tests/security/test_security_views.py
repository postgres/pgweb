from django.test import TestCase, Client


class TestSecurityViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testSecurityIndexViewIsResolved(self):
        response = self.client.get('/support/security', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'security/security.html')
