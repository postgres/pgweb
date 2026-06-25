import os
import os.path

import yaml

from pgweb.util.versions import ParsedVersion


def determine_release_type(release):
    if any(v for v in release['versions'] if v.type == 'major'):
        if len(release['versions']) != 1:
            raise Exception("Major versions should have exactly one version listed")
        return 'major'
    elif len(release['versions']) == 1:
        # A single release, so just copy the type
        return release['versions'][0].type
    else:
        # Any case of >1 release is treated like a minor
        return 'minor'


class Release:
    def __init__(self):
        self._current_release = None
        self._current_release_file = None
        self._current_release_file_timestamp = None

    def get(self):
        from pgweb.news.models import NewsArticle

        currname = self._get_current_release_filename()

        if self._current_release_file and self._current_release_file_timestamp and self._current_release_file == currname and self._current_release_file_timestamp == os.stat(currname).st_mtime:
            # We have it loaded and there has been no changes
            return self._current_release

        # Either we haven't loaded yet, or it has changed, so reload
        self._current_release_file = currname
        self._current_release_file_timestamp = os.stat(currname).st_mtime
        with open(self._current_release_file) as f:
            self._current_release = yaml.load(f, Loader=yaml.SafeLoader)
            self._current_release['versions'] = [ParsedVersion(str(v)) for v in self._current_release['versions']]
            try:
                self._current_release['type'] = determine_release_type(self._current_release)
            except Exception:
                self._current_release['type'] = 'unknown'
            newsid = self._current_release.get('news', {}).get('id', None)
            if newsid:
                try:
                    self._current_release['news']['url'] = NewsArticle.objects.only('id', 'title').get(pk=self._current_release['news']['id']).permanenturl
                except NewsArticle.DoesNotExist:
                    self._current_release['news']['url'] = '/about/news/{}/'.format(self._current_release['news']['id'])

        return self._current_release

    def _get_current_release_filename(self):
        basepath = os.path.abspath(os.path.join(__file__, '../../../data/releases'))
        return os.path.join(basepath, max(f for f in os.listdir(basepath) if f.endswith('.yaml')))


CurrentRelease = Release()
