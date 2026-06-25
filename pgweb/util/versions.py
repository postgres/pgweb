import re

from pgweb.core.models import TESTING_SHORTSTRING

_re_majorminor = re.compile(r'^(\d+)\.(\d+)$')
_re_prerelease = re.compile(r'^(\d+)(alpha|beta|rc)(\d+)$')


class ParsedVersion:
    def __init__(self, versionstr):
        if m := _re_majorminor.match(versionstr):
            self.major, self.minor = map(int, m.groups())
            if self.minor == 0:
                self.type = "major"
            else:
                self.type = "minor"
            self.testing = 0
        elif m := _re_prerelease.match(versionstr):
            self.major = int(m.group(1))
            self.type = m.group(2)
            self.minor = int(m.group(3))
            self.testing = TESTING_SHORTSTRING.index(self.type)
        else:
            raise Exception("Could not parse version string '{}'".format(versionstr))

    def __str__(self):
        if self.type == 'major':
            return str(self.major)
        elif self.type == 'minor':
            return "{}.{}".format(self.major, self.minor)
        else:
            return "{} {} {}".format(self.major, self.type.capitalize(), self.minor)

    def __gt__(self, other):
        # gt operator is required to do max()
        return str(self).__gt__(str(other))
