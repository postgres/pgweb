from django.test import TestCase, Client


class TestPugsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pugs_view_is_resolved(self):
        response = self.client.get('/community/user-groups', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'pugs/index.html')
