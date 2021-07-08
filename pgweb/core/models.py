from django.db import models
from django.core.validators import ValidationError
from django.contrib.auth.models import User
from pgweb.util.misc import varnish_purge

import base64
from decimal import Decimal

from pgweb.util.moderation import TwostateModerateModel

TESTING_CHOICES = (
    (0, 'Release'),
    (1, 'Release candidate'),
    (2, 'Beta'),
    (3, 'Alpha'),
)
TESTING_SHORTSTRING = ('', 'rc', 'beta', 'alpha')


class Version(models.Model):
    tree = models.DecimalField(max_digits=3, decimal_places=1, null=False, blank=False, unique=True)
    latestminor = models.IntegerField(null=False, blank=False, default=0, help_text="For testing versions, latestminor means latest beta/rc number. For other releases, it's the latest minor release number in the tree.")
    reldate = models.DateField(null=False, blank=False)
    current = models.BooleanField(null=False, blank=False, default=False)
    supported = models.BooleanField(null=False, blank=False, default=True)
    testing = models.IntegerField(null=False, blank=False, default=0, help_text="Testing level of this release. latestminor indicates beta/rc number", choices=TESTING_CHOICES)
    docsloaded = models.DateTimeField(null=True, blank=True, help_text="The timestamp of the latest docs load. Used to control indexing and info on developer docs.")
    firstreldate = models.DateField(null=False, blank=False, help_text="The date of the .0 release in this tree")
    eoldate = models.DateField(null=False, blank=False, help_text="The final release date for this tree")

    def __str__(self):
        return self.versionstring

    @property
    def versionstring(self):
        return self.buildversionstring(self.latestminor)

    @property
    def numtree(self):
        # Return the proper numeric tree version, taking into account that PostgreSQL 10
        # changed from x.y to x for major version.
        if self.tree >= 10:
            return int(self.tree)
        else:
            return self.tree

    @property
    def relnotes(self):
        if self.tree >= Decimal('8.2'):
            return 'release-{}-{}.html'.format(str(self.numtree).replace('.', '-'), self.latestminor)
        elif self.tree >= Decimal('7.1'):
            return 'release.html'
        elif self.tree >= Decimal('6.4'):
            return 'release.htm'
        elif self.tree >= Decimal('6.3'):
            return 'c2701.htm'
        else:
            # Should never happen so return something broken
            return 'x'

    def buildversionstring(self, minor):
        if not self.testing:
            return "%s.%s" % (self.numtree, minor)
        else:
            return "%s%s%s" % (self.numtree, TESTING_SHORTSTRING[self.testing], minor)

    @property
    def treestring(self):
        if not self.testing:
            return "%s" % self.numtree
        else:
            return "%s %s" % (self.numtree, TESTING_SHORTSTRING[self.testing])

    def save(self, *args, **kwargs):
        # Make sure only one version at a time can be the current one.
        # (there may be some small race conditions here, but the likelyhood
        # that two admins are editing the version list at the same time...)
        if self.current:
            previous = Version.objects.filter(current=True)
            for p in previous:
                if not p == self:
                    p.current = False
                    p.save()  # primary key check avoids recursion

        # Now that we've made any previously current ones non-current, we are
        # free to save this one.
        super(Version, self).save()

    class Meta:
        ordering = ('-tree', )

    def purge_urls(self):
        yield '/$'
        yield '/support/versioning'
        yield '/support/security'
        yield '/about/featurematrix/$'
        yield '/versions.rss'
        yield '/versions.json'

    def purge_xkeys(self):
        yield 'pgdocs_all'


class Country(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    tld = models.CharField(max_length=3, null=False, blank=False)

    class Meta:
        db_table = 'countries'
        ordering = ('name',)
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class Language(models.Model):
    # Import data from http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    # (yes, there is a UTF16 BOM in the UTF8 file)
    # (and yes, there is a 7 length value in a field specified as 3 chars)
    alpha3 = models.CharField(max_length=7, null=False, blank=False, primary_key=True)
    alpha3term = models.CharField(max_length=3, null=False, blank=True)
    alpha2 = models.CharField(max_length=2, null=False, blank=True)
    name = models.CharField(max_length=100, null=False, blank=False)
    frenchname = models.CharField(max_length=100, null=False, blank=False)

    class Meta:
        ordering = ('name', )

    def __str__(self):
        return self.name


class OrganisationType(models.Model):
    typename = models.CharField(max_length=32, null=False, blank=False)

    def __str__(self):
        return self.typename


_mail_template_choices = (
    ('default', 'Default template'),
    ('pgproject', 'PostgreSQL project news'),
)


class Organisation(TwostateModerateModel):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    address = models.TextField(null=False, blank=True)
    url = models.URLField(null=False, blank=False)
    orgtype = models.ForeignKey(OrganisationType, null=False, blank=False, verbose_name="Organisation type", on_delete=models.CASCADE)
    managers = models.ManyToManyField(User, blank=False)
    mailtemplate = models.CharField(max_length=50, null=False, blank=False, default='default', choices=_mail_template_choices,
                                    verbose_name='Mail template')
    fromnameoverride = models.CharField(max_length=100, null=False, blank=True,
                                        verbose_name='From name override',
                                        help_text='Always set the sender name of news email to this')
    lastconfirmed = models.DateTimeField(null=False, blank=False, auto_now_add=True)

    account_edit_suburl = 'organisations'
    moderation_fields = ['name', 'address', 'url', 'orgtype', 'managers_string']

    def __str__(self):
        return self.name

    @property
    def title(self):
        return self.name

    class Meta:
        ordering = ('name',)

    @classmethod
    def get_formclass(self):
        from pgweb.core.forms import OrganisationForm
        return OrganisationForm

    @property
    def managers_string(self):
        return ", ".join(["{} {} ({})".format(u.first_name, u.last_name, u.email) for u in self.managers.all()])

    def get_field_description(self, f):
        if f == 'managers_string':
            return 'managers'

    def verify_submitter(self, user):
        return self.managers.filter(pk=user.pk).exists()


class OrganisationEmail(models.Model):
    org = models.ForeignKey(Organisation, null=False, blank=False, on_delete=models.CASCADE)
    address = models.EmailField(null=False, blank=False)
    confirmed = models.BooleanField(null=False, blank=False, default=False)
    token = models.CharField(max_length=100, null=True, blank=True)
    added = models.DateTimeField(null=False, blank=False, auto_now_add=True)

    class Meta:
        ordering = ('org', 'address')
        unique_together = (
            ('org', 'address', ),
        )

    def __str__(self):
        if self.confirmed:
            return self.address
        return "{} (not confirmed yet)".format(self.address)


# Basic classes for importing external RSS feeds, such as planet
class ImportedRSSFeed(models.Model):
    internalname = models.CharField(max_length=32, null=False, blank=False, unique=True)
    url = models.URLField(null=False, blank=False)
    purgepattern = models.CharField(max_length=512, null=False, blank=True, help_text="NOTE! Pattern will be automatically anchored with ^ at the beginning, but you must lead with a slash in most cases - and don't forget to include the trailing $ in most cases")

    def purge_related(self):
        if self.purgepattern:
            varnish_purge(self.purgepattern)

    def __str__(self):
        return self.internalname


class ImportedRSSItem(models.Model):
    feed = models.ForeignKey(ImportedRSSFeed, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False, blank=False)
    url = models.URLField(null=False, blank=False)
    posttime = models.DateTimeField(null=False, blank=False)

    def __str__(self):
        return self.title

    @property
    def date(self):
        return self.posttime.strftime("%Y-%m-%d")


# From man sshd, except for ssh-dss
_valid_keytypes = ['ecdsa-sha2-nistp256', 'ecdsa-sha2-nistp384', 'ecdsa-sha2-nistp521', 'ssh-ed25519', 'ssh-rsa']


# Options, keytype, key, comment. But we don't support options.
def validate_sshkey(key):
    lines = key.splitlines()
    for k in lines:
        pieces = k.split()
        if len(pieces) == 0:
            raise ValidationError("Empty keys are not allowed")
        if len(pieces) > 3:
            raise ValidationError('Paste each ssh key without options, e.g. "ssh-rsa AAAAbbbcc mykey@machine"')
        if pieces[0] == 'ssh-dss':
            raise ValidationError("For security reasons, ssh-dss keys are not supported")
        if pieces[0] not in _valid_keytypes:
            raise ValidationError("Only keys of types {0} are supported, not {1}.".format(", ".join(_valid_keytypes), pieces[0]))
        try:
            base64.b64decode(pieces[1])
        except Exception as e:
            raise ValidationError("Incorrect base64 encoded key!")


# Extra attributes for users (if they have them)
class UserProfile(models.Model):
    user = models.OneToOneField(User, null=False, blank=False, primary_key=True, on_delete=models.CASCADE)
    sshkey = models.TextField(null=False, blank=True, verbose_name="SSH key", help_text="Paste one or more public keys in OpenSSH format, one per line.", validators=[validate_sshkey, ])
    lastmodified = models.DateTimeField(null=False, blank=False, auto_now=True)
    block_oauth = models.BooleanField(null=False, blank=False, default=False,
                                      verbose_name="Block OAuth login",
                                      help_text="Disallow login to this account using OAuth providers like Google or Microsoft.")


# Notifications sent for any moderated content.
# Yes, we uglify it by storing the type of object as a string, so we don't
# end up with a bazillion fields being foreign keys. Ugly, but works.
class ModerationNotification(models.Model):
    objectid = models.IntegerField(null=False, blank=False, db_index=True)
    objecttype = models.CharField(null=False, blank=False, max_length=100)
    text = models.TextField(null=False, blank=False)
    author = models.CharField(null=False, blank=False, max_length=100)
    date = models.DateTimeField(null=False, blank=False, auto_now=True)

    def __str__(self):
        return "%s id %s (%s): %s" % (self.objecttype, self.objectid, self.date, self.text[:50])

    class Meta:
        ordering = ('-date', )
