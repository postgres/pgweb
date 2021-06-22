from django.test import TestCase, Client


class TestCoreViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testHomeViewIsResolved(self):
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def testAboutViewIsResolved(self):
        response = self.client.get('/about', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')

    def testCommunityViewIsResolved(self):
        response = self.client.get('/community', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/community.html')

    def testSupportVersioningViewIsResolved(self):
        response = self.client.get('/support/versioning', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'support/versioning.html')
