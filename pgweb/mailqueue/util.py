from django.db import transaction

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate, formataddr
from email.utils import make_msgid
from email import encoders, charset
from email.header import Header

from .models import QueuedMail, LastSent


def _encoded_email_header(name, email):
    if name:
        return formataddr((str(Header(name, 'utf-8')), email))
    return email


# Default for utf-8 in python is to encode subject with "shortest" and body with "base64". For our texts,
# make it always quoted printable, for easier reading and testing.
_utf8_charset = charset.Charset('utf-8')
_utf8_charset.header_encoding = charset.QP
_utf8_charset.body_encoding = charset.QP


def send_simple_mail(sender, receiver, subject, msgtxt, attachments=None, usergenerated=False, cc=None, replyto=None, sendername=None, receivername=None, messageid=None, suppress_auto_replies=True, is_auto_reply=False, htmlbody=None, headers={}, staggertype=None, stagger=None):
    # attachment format, each is a tuple of (name, mimetype,contents)
    # content should be *binary* and not base64 encoded, since we need to
    # use the base64 routines from the email library to get a properly
    # formatted output message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = _encoded_email_header(receivername, receiver)
    msg['From'] = _encoded_email_header(sendername, sender)
    if cc:
        msg['Cc'] = cc
    if replyto:
        msg['Reply-To'] = replyto
    msg['Date'] = formatdate(localtime=True)
    if messageid:
        msg['Message-ID'] = messageid
    else:
        msg['Message-ID'] = make_msgid()
    if suppress_auto_replies:
        # Do our best to set some headers to indicate that auto-replies like out of office
        # messages should not be sent to this email.
        msg['X-Auto-Response-Suppress'] = 'All'

    # Is this email auto-generated or auto-replied?
    if is_auto_reply:
        msg['Auto-Submitted'] = 'auto-replied'
    elif not usergenerated:
        msg['Auto-Submitted'] = 'auto-generated'

    for h, v in headers.items():
        if h in msg:
            # Replace the existing header -- the one specified is supposedly overriding it
            msg.replace_header(h, v)
        else:
            msg.add_header(h, v)

    if htmlbody:
        mpart = MIMEMultipart("alternative")
        mpart.attach(MIMEText(msgtxt, _charset=_utf8_charset))
        mpart.attach(MIMEText(htmlbody, 'html', _charset=_utf8_charset))
        msg.attach(mpart)
    else:
        # Just a plaintext body, so append it directly
        msg.attach(MIMEText(msgtxt, _charset='utf-8'))

    if attachments:
        for a in attachments:
            main, sub = a['contenttype'].split('/')
            part = MIMENonMultipart(main, sub)
            part.set_payload(a['content'])
            part.add_header('Content-Disposition', a.get('disposition', 'attachment; filename="%s"' % a['filename']))
            if 'id' in a:
                part.add_header('Content-ID', a['id'])

            encoders.encode_base64(part)
            msg.attach(part)

    with transaction.atomic():
        if staggertype and stagger:
            # Don't send a second one too close after another one of this class.
            ls, created = LastSent.objects.get_or_create(type=staggertype, defaults={'lastsent': datetime.now()})

            sendat = ls.lastsent = ls.lastsent + stagger
            ls.save(update_fields=['lastsent'])
        else:
            sendat = datetime.now()

        # Just write it to the queue, so it will be transactionally rolled back
        QueuedMail(sender=sender, receiver=receiver, fullmsg=msg.as_string(), usergenerated=usergenerated, sendat=sendat).save()
        if cc:
            # Write a second copy for the cc, wihch will be delivered
            # directly to the recipient. (The sender doesn't parse the
            # message content to extract cc fields).
            QueuedMail(sender=sender, receiver=cc, fullmsg=msg.as_string(), usergenerated=usergenerated, sendat=sendat).save()
