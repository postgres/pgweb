from django.test import TestCase, Client


class TestEventsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testEventsViewIsResolved(self):
        response = self.client.get('/about/events', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/archive.html')

    def testEventArchiveViewIsResolved(self):
        response = self.client.get('/about/eventarchive', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/archive.html')
