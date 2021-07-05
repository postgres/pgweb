from django.test import TestCase, Client


class TestSecurityViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_security_index_view_is_resolved(self):
        response = self.client.get('/support/security', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'security/security.html')
