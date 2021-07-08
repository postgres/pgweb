import factory
from factory.django import DjangoModelFactory
from pgweb.core.models import Version, UserProfile, Organisation, OrganisationEmail, OrganisationType, OrganisationEmail, ImportedRSSFeed, ImportedRSSItem
from pgweb.quotes.models import Quote
from django.contrib.auth.models import User
import datetime


class VersionFactory(DjangoModelFactory):
    class Meta:
        model = Version

    tree = 13.3
    latestminor = 0
    reldate = datetime.datetime.today()
    current = False
    supported = True
    testing = 0
    docsloaded = datetime.datetime.now()
    firstreldate = datetime.datetime.today()
    eoldate = datetime.datetime.today()


class QuoteFactory(DjangoModelFactory):
    class Meta:
        model = Quote

    approved = False
    quote = "Test"
    who = "test name"
    org = "PostgreSQL"
    link = "https://postgresql.org"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Faker('email')
    password = factory.Faker('password')
    is_staff = False
    is_superuser = False


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    sshkey = ""
    block_oauth = False


class OrganisationTypeFactory(DjangoModelFactory):
    class Meta:
        model = OrganisationType

    typename = "test"


class OrganisationFactory(DjangoModelFactory):
    class Meta:
        model = Organisation

    name = "PostgreSQL"
    address = "test address"
    url = "https://www.postgresql.org/"
    orgtype = factory.SubFactory(OrganisationTypeFactory)

    @factory.post_generation
    def managers(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for user in extracted:
                self.managers.add(user)
    mailtemplate = "default"


class OrganisationEmailFactory(DjangoModelFactory):
    class Meta:
        model = OrganisationEmail

    org = factory.SubFactory(OrganisationFactory)
    address = factory.Faker('address')
    confirmed = False
    token = factory.Faker('first_name')


class ImportedRSSFeedFactory(DjangoModelFactory):
    class Meta:
        model = ImportedRSSFeed

    internalname = "planet"
    url = "https://www.postgresql.org/"
    purgepattern = "/"


class ImportedRSSItemFactory(DjangoModelFactory):
    class Meta:
        model = ImportedRSSItem

    feed = factory.SubFactory(ImportedRSSFeedFactory)
    title = "title"
    url = "https://www.postgresql.org/"
    posttime = datetime.datetime.now()
