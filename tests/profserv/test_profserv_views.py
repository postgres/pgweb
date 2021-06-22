from django.test import TestCase, Client


class TestProfServViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testProfservSupportViewIsResolved(self):
        response = self.client.get('/support/professional_support', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/root.html')

    def testProfservHostingViewIsResolved(self):
        response = self.client.get('/support/professional_hosting', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/root.html')

    def testProfservAfricaViewIsResolved(self):
        response = self.client.get('/support/professional_hosting/africa', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def testProfservEuropeViewIsResolved(self):
        response = self.client.get('/support/professional_hosting/europe', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def testProfservNorthAmreicaViewIsResolved(self):
        response = self.client.get('/support/professional_hosting/northamerica', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def testProfservOceaniaViewIsResolved(self):
        response = self.client.get('/support/professional_hosting/oceania', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def testProfservSouthAmericaViewIsResolved(self):
        response = self.client.get('/support/professional_hosting/southamerica', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')
