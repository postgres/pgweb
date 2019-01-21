from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate, formataddr
from email.utils import make_msgid
from email import encoders
from email.header import Header

from .models import QueuedMail


def _encoded_email_header(name, email):
    if name:
        return formataddr((str(Header(name, 'utf-8')), email))
    return email


def send_simple_mail(sender, receiver, subject, msgtxt, attachments=None, usergenerated=False, cc=None, replyto=None, sendername=None, receivername=None, messageid=None):
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

    msg.attach(MIMEText(msgtxt, _charset='utf-8'))

    if attachments:
        for filename, contenttype, content in attachments:
            main, sub = contenttype.split('/')
            part = MIMENonMultipart(main, sub)
            part.set_payload(content)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % filename)
            encoders.encode_base64(part)
            msg.attach(part)

    # Just write it to the queue, so it will be transactionally rolled back
    QueuedMail(sender=sender, receiver=receiver, fullmsg=msg.as_string(), usergenerated=usergenerated).save()
    if cc:
        # Write a second copy for the cc, wihch will be delivered
        # directly to the recipient. (The sender doesn't parse the
        # message content to extract cc fields).
        QueuedMail(sender=sender, receiver=cc, fullmsg=msg.as_string(), usergenerated=usergenerated).save()


def send_mail(sender, receiver, fullmsg, usergenerated=False):
    # Send an email, prepared as the full MIME encoded mail already
    QueuedMail(sender=sender, receiver=receiver, fullmsg=fullmsg, usergenerated=False).save()
