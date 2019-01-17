# Yes, this is trivial, but we might want to put something
# more here in the future :)
import datetime


def log(msg):
    print "%s: %s" % (datetime.datetime.now(), msg)
