import factory
from factory.django import DjangoModelFactory
from pgweb.news.models import NewsTag, NewsArticle
from ..core.factories import OrganisationFactory, OrganisationEmailFactory
import datetime


class NewsTagFactory(DjangoModelFactory):
    class Meta:
        model = NewsTag

    urlname = factory.Sequence(lambda n: 'test%s' % n)
    name = factory.Sequence(lambda n: 'Test %s' % n)
    description = factory.Faker('sentence')

    @factory.post_generation
    def allowed_orgs(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for organisation in extracted:
                self.allowed_orgs.add(organisation)
    sortkey = 100


class NewsArticleFactory(DjangoModelFactory):
    class Meta:
        model = NewsArticle

    org = factory.SubFactory(OrganisationFactory)
    email = factory.SubFactory(OrganisationEmailFactory)
    date = datetime.datetime.today()
    title = "test title"
    content = factory.Faker('sentence')
    tweeted = False

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for tag in extracted:
                self.tags.add(tag)
