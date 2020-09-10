from django.template.loader import get_template
from django.conf import settings

import os
import hmac
import hashlib
import re
import base64
from email.utils import formatdate
from email.utils import make_msgid

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


def render_news_template(news):
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
                'mimetype': _get_contenttype_from_extension(f),
                'contenttype': '{}; name={}'.format(_get_contenttype_from_extension(f), f),
                'filename': f,
                'disposition': 'inline; filename="{}"'.format(f),
                'id': '<{}>'.format(f),
            }
            with open(os.path.join(basedir, f), "rb") as f:
                a['content'] = f.read()
            attachments.append(a)

    return html, attachments


_re_img = re.compile(r'(<img[^>]+src=")(cid:[^"]+)("[^>]+>)', re.I)


def embed_images_in_html(html, attachments):
    amap = {a['filename']: a for a in attachments}

    def _replace_cid_reference(t):
        a = amap[t.group(2).replace('cid:', '')]
        datasrc = 'data:{};base64,{}'.format(a['mimetype'], base64.b64encode(a['content']).decode('ascii'))
        return t.group(1) + datasrc + t.group(3)

    return _re_img.sub(_replace_cid_reference, html)


def send_news_email(news):
    html, attachments = render_news_template(news)

    messageid = make_msgid()

    # If configured to, add the tags and sign them so that a pglister delivery system can filter
    # recipients based on it.
    if settings.NEWS_MAIL_TAGKEY:
        date = formatdate(localtime=True)
        tagstr = ",".join([t.urlname for t in news.tags.all()])
        h = hmac.new(
            settings.NEWS_MAIL_TAGKEY.encode('ascii'),
            tagstr.encode('ascii') + messageid.encode('ascii') + date.encode('ascii'),
            hashlib.sha256
        )
        headers = {
            'X-pglister-tags': tagstr,
            'X-pglister-tagsig': h.hexdigest(),
            'Date': date,
        }
    else:
        headers = {}

    send_simple_mail(
        settings.NEWS_MAIL_SENDER,
        settings.NEWS_MAIL_RECEIVER,
        news.title,
        news.content,
        replyto=news.email.address,
        sendername=news.sentfrom,
        receivername=settings.NEWS_MAIL_RECEIVER_NAME,
        messageid=messageid,
        htmlbody=html,
        attachments=attachments,
        headers=headers,
        usergenerated=True,
    )
