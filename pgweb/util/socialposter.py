#
# NOTE! This file is intended to be shared between multiple projects so should contain
# no project specific knowledge!
#

from datetime import datetime, timezone
import io
import re
from urllib.parse import urlparse

import requests
import requests_oauthlib


class SocialPoster:
    def __init__(self, settings):
        self.settings = settings

    def post(self):
        raise NotImplementedError

    def register(self, clientname):
        raise NotImplementedError

    def set_pin(self, postid):
        raise NotImplementedError


class Mastodon(SocialPoster):
    name = 'mastodon'

    def post(self, text):
        r = requests.post(
            '{}/api/v1/statuses'.format(self.settings.MASTODON_BASEURL),
            headers={'Authorization': 'Bearer {}'.format(self.settings.MASTODON_TOKEN)},
            json={
                'status': text,
                'visibility': 'public',
            },
            timeout=10,
        )
        if r.status_code != 200:
            print("Failed to post to mastodon: {}".format(r.text))
            return None

        return r.json()['id']

    def set_pin(self, postid):
        # First we have to see if there is an existing pin that has to be removed. To do that, we
        # have to fetch our account id.
        r = requests.get(
            '{}/api/v1/accounts/verify_credentials'.format(self.settings.MASTODON_BASEURL),
            headers={'Authorization': 'Bearer {}'.format(self.settings.MASTODON_TOKEN)},
            timeout=10,
        )
        if r.status_code != 200:
            print("Failed to get mastodon credentials: {}".format(r.text))
            return False

        # Next, get the currently pinned ones
        r = requests.get(
            '{}/api/v1/accounts/{}/statuses'.format(self.settings.MASTODON_BASEURL, r.json()['id']),
            headers={'Authorization': 'Bearer {}'.format(self.settings.MASTODON_TOKEN)},
            params={'pinned': 'true'},
            timeout=10,
        )
        if r.status_code != 200:
            print("Failed to get list of mastodon pins: {}".format(r.text))
            return False

        found = False
        for p in r.json():
            if p['id'] == postid:
                # Already pinned!
                found = True
            else:
                # This should be unpinned
                r2 = requests.post(
                    '{}/api/v1/statuses/{}/unpin'.format(self.settings.MASTODON_BASEURL, p['id']),
                    headers={'Authorization': 'Bearer {}'.format(self.settings.MASTODON_TOKEN)},
                    timeout=10,
                )
                if r2.status_code != 200:
                    print("Failed to unpin from mastodon: {}".format(r2.text))

        if not found and postid is not None:
            # Not already pinned, so pin!
            r2 = requests.post(
                '{}/api/v1/statuses/{}/pin'.format(self.settings.MASTODON_BASEURL, postid),
                headers={'Authorization': 'Bearer {}'.format(self.settings.MASTODON_TOKEN)},
                timeout=10,
            )
            if r2.status_code != 200:
                print("Failed to pin to mastodon: {}".format(r2.text))
                return False

        return True

    def register(self, clientname):
        toadd = io.StringIO()

        if getattr(self.settings, 'MASTODON_BASEURL', None) is None or \
           getattr(self.settings, 'MASTODON_CLIENTID', None) is None or \
           getattr(self.settings, 'MASTODON_CLIENTSECRET', None) is None:
            while True:
                baseurl = input("Enter base URL (e.g. https://mastodon.social): ").rstrip('/')
                p = urlparse(baseurl)
                if p.scheme != 'https':
                    print("Only https supported")
                    continue
                break

            # Mastodon requires us to have a client id/secret, but we can just register it
            r = requests.post('{}/api/v1/apps'.format(baseurl), {
                'client_name': clientname,
                'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
                'scopes': 'read write:statuses write:media write:accounts',
            })
            r.raise_for_status()

            j = r.json()
            clientid = j['client_id']
            clientsecret = j['client_secret']

            print("Add the following to your local settings:")
            toadd.write("MASTODON_BASEURL='{}'\n".format(baseurl))
            toadd.write("MASTODON_CLIENTID='{}'\n".format(clientid))
            toadd.write("MASTODON_CLIENTSECRET='{}'\n".format(clientsecret))
        else:
            baseurl = self.settings.MASTODON_BASEURL
            clientid = self.settings.MASTODON_CLIENTID
            clientsecret = self.settings.MASTODON_CLIENTSECRET

        if getattr(self.settings, 'MASTODON_TOKEN', None) is None:
            session = requests_oauthlib.OAuth2Session(clientid, redirect_uri='urn:ietf:wg:oauth:2.0:oob', scope='read write:statuses write:media write:accounts')

            url, state = session.authorization_url("{}/oauth/authorize".format(baseurl))
            print("Please visit {} and log in.".format(url))
            code = input("Enter the code received: ")

            tokens = session.fetch_token(
                '{}/oauth/token'.format(baseurl),
                code=code.strip(),
                client_secret=clientsecret,
                scopes='read write:statuses write:media write:accounts',
            )

            toadd.write("MASTODON_TOKEN='{}'\n".format(tokens['access_token']))

        return toadd.getvalue()


class Bluesky(SocialPoster):
    # Bluesky tokens are short lived, but we just assume they are long lived enough for this script to complete
    # (normally seconds vs a lifetime in minutes). So just cache the access token.
    name = 'bluesky'

    def __init__(self, settings):
        super().__init__(settings)
        self._token = None
        self._repo = None

    @property
    def token(self):
        if not self._token:
            self._get_token_and_repo()
        return self._token

    @property
    def repo(self):
        if not self._repo:
            self._get_token_and_repo()
        return self._repo

    def _get_token_and_repo(self):
        r = requests.post('https://bsky.social/xrpc/com.atproto.server.createSession', json={
            'identifier': self.settings.BLUESKY_USER,
            'password': self.settings.BLUESKY_PASSWORD,
        }, timeout=10)
        r.raise_for_status()
        self._token = r.json()['accessJwt']
        self._repo = r.json()['did']

    def post(self, text):
        post = {
            '$type': 'app.bsky.feed.post',
            'text': text,
            'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        }
        facets = list(self._parse_facets(text.encode('utf-8')))
        if facets:
            post['facets'] = facets

        r = requests.post(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            headers={'Authorization': 'Bearer {}'.format(self.token)},
            json={
                'repo': self.repo,
                'collection': 'app.bsky.feed.post',
                'record': post,
            },
            timeout=10,
        )
        if r.status_code == 400 and r.headers.get('content-type').startswith('application/json'):
            print("Failed to post to bluesky: {}, message {}".format(r.json()['error'], r.json()['message']))
            return None
        if r.status_code != 200:
            print("Failed to post to bluesky: {}".format(r.text))
            return None

        return r.json()['uri']

    def set_pin(self, postid):
        # Get our profile, so we can "patch" it
        r = requests.get(
            'https://bsky.social/xrpc/com.atproto.repo.getRecord',
            headers={'Authorization': 'Bearer {}'.format(self.token)},
            params={'repo': self.repo, 'collection': 'app.bsky.actor.profile', 'rkey': 'self'},
            timeout=10,
        )
        if r.status_code != 200:
            print("Failed to get bluesky profile: {}".format(r.text))
            return False
        record = r.json()['value']
        if postid:
            # We have the uri, but we need both the uri and the cid, so fetch the post
            r2 = requests.get(
                'https://bsky.social/xrpc/app.bsky.feed.getPosts',
                headers={'Authorization': 'Bearer {}'.format(self.token)},
                params={'uris': postid},
                timeout=10,
            )
            if r.status_code != 200:
                print("Failed to read back bluesky post {}: {}".format(postid, r.text))
                return False

            cid = r2.json()['posts'][0]['cid']

            record['pinnedPost'] = {
                'uri': postid,
                'cid': cid,
            }
        else:
            if 'pinnedPost' in record:
                del record['pinnedPost']

        if record != r.json()['value']:
            # Some changes, so we need to update
            r = requests.post(
                'https://bsky.social/xrpc/com.atproto.repo.putRecord',
                headers={'Authorization': 'Bearer {}'.format(self.token)},
                json={'repo': self.repo, 'collection': 'app.bsky.actor.profile', 'rkey': 'self', 'record': record},
                timeout=10,
            )
            if r.status_code != 200:
                print("Failed to save pack bluesky profile for pinned posts: {}".format(r.text))
                return False
            return True

        return True

    def register(self, clientname):
        if getattr(self.settings, 'BLUESKY_USER', None) is None or getattr(self.settings, 'BLUESKY_PASSWORD', None) is None:
            return "For bluesky, add an 'app password' from 'Settings' -> 'Privacy and Security'.\nRegister the account email as BLUESKY_USER and the app password as BLUESKY_PASSWORD.\n"
        return ''

    # Adapted from Bluesky examples
    _facet_parsers = (
        ('app.bsky.richtext.facet#link', 'uri', re.compile(rb"\s+(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"), 0, 0),
        ('app.bsky.richtext.facet#tag', 'tag', re.compile(rb'\s+#(\w+)'), -1, 0),
    )

    def _parse_facets(self, text: bytes):
        """
        parses post text and returns a list of app.bsky.richtext.facet objects for any URLs (https://example.com) or hashtags

        indexing must work with UTF-8 encoded bytestring offsets, not regular unicode string offsets, to match Bluesky API expectations
        """
        for t, f, r, startofs, endofs in self._facet_parsers:
            for m in r.finditer(text):
                yield {
                    "index": {
                        "byteStart": m.start(1) + startofs,
                        "byteEnd": m.end(1) + endofs,
                    },
                    "features": [{"$type": t, f: m.group(1).decode("UTF-8")}],
                }


def get_all_providers(settings, returnallproviders=False):
    allproviders = []
    if returnallproviders or settings is None or getattr(settings, 'MASTODON_BASEURL', None) is not None:
        allproviders.append(Mastodon(settings))
    if returnallproviders or settings is None or getattr(settings, 'BLUESKY_USER', None) is not None:
        allproviders.append(Bluesky(settings))

    return allproviders, [p.name for p in allproviders]
