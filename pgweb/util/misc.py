from subprocess import Popen, PIPE
from email.mime.text import MIMEText

from pgweb.util.helpers import template_to_string

def prettySize(size):
	if size < 1024:
		return "%s bytes" % size
	suffixes = [("bytes",2**10), ("KB",2**20), ("MB",2**30), ("GB",2**40), ("TB",2**50)]
	for suf, lim in suffixes:
		if size > lim:
			continue
		else:
			return "%s %s" % (round(size/float(lim/2**10),2).__str__(),suf)

def sendmail(msg):
	pipe = Popen("sendmail -t", shell=True, stdin=PIPE).stdin
	pipe.write(msg.as_string())
	pipe.close()

def send_template_mail(sender, receiver, subject, templatename, templateattr={}):
	msg = MIMEText(
		template_to_string(templatename, templateattr),
		_charset='utf-8')
	msg['Subject'] = subject
	msg['To'] = receiver
	msg['From'] = sender
	sendmail(msg)

