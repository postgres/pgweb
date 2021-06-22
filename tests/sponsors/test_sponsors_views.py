from django.test import TestCase, Client


class TestSponsorsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testSponsorsViewIsResolved(self):
        response = self.client.get('/about/sponsors', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'sponsors/sponsors.html')

    def testServersViewIsResolved(self):
        response = self.client.get('/about/servers', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'sponsors/servers.html')
