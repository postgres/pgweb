from django.test import TestCase, Client


class TestCoreViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testCommunityViewIsResolved(self):
        response = self.client.get('/community/contributors', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'contributors/list.html')

    def testListViewIsRedirected(self):
        response = self.client.get('/community/lists')
        self.assertEquals(response.status_code, 301)

    def testListSubscribeViewIsRedirected(self):
        response = self.client.get('/community/lists/subscribe')
        self.assertEquals(response.status_code, 301)
