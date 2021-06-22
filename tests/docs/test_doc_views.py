from django.test import TestCase, Client


class TestDocsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def testDocViewIsResolved(self):
        response = self.client.get('/docs', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/index.html')

    def testDocManualViewIsRedirected(self):
        response = self.client.get('/docs/manuals')
        self.assertEquals(response.status_code, 301)

    def testDocManualViewIsRedirectedToRoot(self):
        response = self.client.get('/docs/manuals', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/index.html')

    def testDocManualsArchiveViewIsResolved(self):
        response = self.client.get('/docs/manuals/archive', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/archive.html')

    def testDocReleaseViewIsResolved(self):
        response = self.client.get('/docs/release', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/release_notes.html')
