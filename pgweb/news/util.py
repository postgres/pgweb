from django.template.loader import get_template
from django.conf import settings

import os
import hmac
import hashlib

from pgweb.mailqueue.util import send_simple_mail


def _get_contenttype_from_extension(f):
    _map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
    }
    e = os.path.splitext(f)[1][1:]
    if e not in _map:
        raise Exception("Unknown extension {}".format(e))
    return _map[e]


def send_news_email(news):
    # To generate HTML email, pick a template based on the organisation and render it.

    html = get_template('news/mail/{}.html'.format(news.org.mailtemplate)).render({
        'news': news,
    })

    # Enumerate all files for this template, if any
    attachments = []
    basedir = os.path.abspath(os.path.join(settings.PROJECT_ROOT, '../templates/news/mail/img.{}'.format(news.org.mailtemplate)))
    if os.path.isdir(basedir):
        for f in os.listdir(basedir):
            a = {
                'contenttype': '{}; name={}'.format(_get_contenttype_from_extension(f), f),
                'filename': f,
                'disposition': 'inline; filename="{}"'.format(f),
                'id': '<{}>'.format(f),
            }
            with open(os.path.join(basedir, f), "rb") as f:
                a['content'] = f.read()
            attachments.append(a)

    # If configured to, add the tags and sign them so that a pglister delivery system can filter
    # recipients based on it.
    if settings.NEWS_MAIL_TAGKEY:
        tagstr = ",".join([t.urlname for t in news.tags.all()])
        h = hmac.new(tagstr.encode('ascii'), settings.NEWS_MAIL_TAGKEY.encode('ascii'), hashlib.sha256)
        headers = {
            'X-pglister-tags': tagstr,
            'X-pglister-tagsig': h.hexdigest(),
        }
    else:
        headers = {}

    send_simple_mail(
        settings.NEWS_MAIL_SENDER,
        settings.NEWS_MAIL_RECEIVER,
        news.title,
        news.content,
        replyto=news.org.email,
        sendername="PostgreSQL news",  # XXX: Somehow special case based on organisation here as well?
        receivername=settings.NEWS_MAIL_RECEIVER_NAME,
        htmlbody=html,
        attachments=attachments,
        headers=headers,
    )
