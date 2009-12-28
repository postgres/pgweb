from subprocess import Popen, PIPE

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

