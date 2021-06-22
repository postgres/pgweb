from django.test import TestCase, Client


class TestFeaturematrixViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testFeaturesViewIsResolved(self):
        response = self.client.get('/about/featurematrix', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'featurematrix/featurematrix.html')
