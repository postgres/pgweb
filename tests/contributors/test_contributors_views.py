from django.test import TestCase, Client


class TestCoreViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_community_view_is_resolved(self):
        response = self.client.get('/community/contributors', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'contributors/list.html')

    def test_list_view_is_redirected(self):
        response = self.client.get('/community/lists')
        self.assertEquals(response.status_code, 301)

    def test_list_subscribe_view_is_redirected(self):
        response = self.client.get('/community/lists/subscribe')
        self.assertEquals(response.status_code, 301)
