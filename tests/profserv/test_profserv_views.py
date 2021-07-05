from django.test import TestCase, Client


class TestProfServViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_profserv_support_view_is_resolved(self):
        response = self.client.get('/support/professional_support', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/root.html')

    def test_profserv_hosting_view_is_resolved(self):
        response = self.client.get('/support/professional_hosting', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/root.html')

    def test_profserv_africa_view_is_resolved(self):
        response = self.client.get('/support/professional_hosting/africa', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def test_profserv_europe_view_is_resolved(self):
        response = self.client.get('/support/professional_hosting/europe', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def test_profserv_NorthAmerica_view_is_resolved(self):
        response = self.client.get('/support/professional_hosting/northamerica', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def test_profserv_oceania_view_is_resolved(self):
        response = self.client.get('/support/professional_hosting/oceania', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')

    def test_profserv_SouthAmerica_view_is_resolved(self):
        response = self.client.get('/support/professional_hosting/southamerica', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'profserv/list.html')
