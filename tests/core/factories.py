from factory.django import DjangoModelFactory
from pgweb.core.models import Version, Organisation, OrganisationEmail, OrganisationType
from pgweb.quotes.models import Quote
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
