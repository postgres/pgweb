from django.test import TestCase, Client


class TestCoreViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view_is_resolved(self):
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_about_view_is_resolved(self):
        response = self.client.get('/about', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')

    def test_community_view_is_resolved(self):
        response = self.client.get('/community', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/community.html')

    def test_support_versioning_view_is_resolved(self):
        response = self.client.get('/support/versioning', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'support/versioning.html')
