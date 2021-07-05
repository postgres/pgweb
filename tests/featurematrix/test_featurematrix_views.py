from django.test import TestCase, Client


class TestFeaturematrixViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_features_view_is_resolved(self):
        response = self.client.get('/about/featurematrix', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'featurematrix/featurematrix.html')
