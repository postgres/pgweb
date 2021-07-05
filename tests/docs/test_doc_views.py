from django.test import TestCase, Client


class TestDocsViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_doc_view_is_resolved(self):
        response = self.client.get('/docs', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/index.html')

    def test_doc_manual_view_is_redirected(self):
        response = self.client.get('/docs/manuals')
        self.assertEquals(response.status_code, 301)

    def test_doc_manual_view_is_redirected_to_root(self):
        response = self.client.get('/docs/manuals', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/index.html')

    def test_doc_manuals_archive_view_is_resolved(self):
        response = self.client.get('/docs/manuals/archive', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/archive.html')

    def test_doc_release_view_is_resolved(self):
        response = self.client.get('/docs/release', {}, True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'docs/release_notes.html')
