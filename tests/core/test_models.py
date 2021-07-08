import pytest
import random
import string
from .factories import QuoteFactory, VersionFactory, UserProfileFactory, OrganisationFactory, UserFactory, OrganisationEmailFactory
from django.test import TestCase
from pgweb.core.models import Country, Language, ModerationNotification, Version, UserProfile, Organisation
import datetime


@pytest.mark.django_db
class TestQuotesModel(TestCase):
    def setUp(self):
        self.quote = QuoteFactory()
        self.randomString = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=100))
        self.largerQuote = QuoteFactory(quote=self.randomString)

    def test_quote_display_name(self):
        self.assertEquals(str(self.quote), self.quote.quote)

    def test_max_quote_display_name_length(self):
        self.assertNotEquals(str(self.largerQuote), self.largerQuote.quote)
        self.assertEquals(len(str(self.largerQuote)), 78)
        self.assertEquals(str(self.largerQuote)[-3:], '...')


@pytest.mark.django_db
class TestVersionModel(TestCase):
    def setUp(self):
        self.version = VersionFactory()
        self.testing_version_rc = VersionFactory(tree=12.1, testing=1, latestminor=1)
        self.testing_version_beta = VersionFactory(tree=12.2, testing=2, latestminor=2)
        self.testing_version_alpha = VersionFactory(tree=12.3, testing=3, latestminor=3)

    def test_instance_of_model(self):
        self.assertIsInstance(self.version, Version)

    def test_version_greater_than_10(self):
        assert str(self.version) == "13.0"
        assert self.version.treestring == "13"
        assert self.version.relnotes == "release-13-0.html"

    def test_rc_testing_version_greater_than_10(self):
        assert str(self.testing_version_rc) == "12rc1"
        assert self.testing_version_rc.treestring == "12 rc"
        assert self.testing_version_rc.relnotes == "release-12-1.html"

    def test_beta_testing_version_greater_than_10(self):
        assert str(self.testing_version_beta) == "12beta2"
        assert self.testing_version_beta.treestring == "12 beta"
        assert self.testing_version_beta.relnotes == "release-12-2.html"

    def test_alpha_testing_version_greater_than_10(self):
        assert str(self.testing_version_alpha) == "12alpha3"
        assert self.testing_version_alpha.treestring == "12 alpha"
        assert self.testing_version_alpha.relnotes == "release-12-3.html"


@pytest.mark.django_db
class TestUserProfileModel(TestCase):
    def setUp(self):
        self.user = UserProfileFactory()

    def test_user_profile_instance(self):
        self.assertIsInstance(self.user, UserProfile)


@pytest.mark.django_db
class OrganisationModel(TestCase):
    def setUp(self):
        self.user = UserFactory(first_name="John", last_name="Doe", email="johndoe@test.com")
        self.user_not_manager = UserFactory()
        self.organisation = OrganisationFactory(name="PostgreSQL", managers=[self.user])
        self.organisation_email = OrganisationEmailFactory(org=self.organisation, address="test address")
        self.organisation_email_confirmed = OrganisationEmailFactory(org=self.organisation, address="test address 1", confirmed=True)

    def test_organisation_instance(self):
        self.assertIsInstance(self.organisation, Organisation)

    def test_organisation_type_name(self):
        self.assertEquals(str(self.organisation.orgtype), "test")

    def test_organisation_display_name(self):
        self.assertEquals(str(self.organisation), "PostgreSQL")
        self.assertEquals(self.organisation.title, "PostgreSQL")

    def test_managers_string_property(self):
        self.assertEquals(self.organisation.managers_string, "John Doe (johndoe@test.com)")

    def test_verify_submitters(self):
        self.assertEquals(self.organisation.verify_submitter(self.user_not_manager), False)
        self.assertEquals(self.organisation.verify_submitter(self.user), True)

    def test_get_field_description(self):
        self.assertEquals(self.organisation.get_field_description("managers_string"), "managers")
        self.assertEquals(self.organisation.get_field_description("random"), None)

    def test_organisation_mail(self):
        self.assertEquals(str(self.organisation_email), "test address (not confirmed yet)")
        self.assertEquals(str(self.organisation_email_confirmed), "test address 1")


@pytest.mark.django_db
def test_country_model():
    country = Country.objects.create(name="Test Country", tld="TST")
    assert str(country) == country.name


@pytest.mark.django_db
def test_language_model():
    language = Language.objects.create(alpha3="test",
                                       name="test language",
                                       frenchname="french")
    assert str(language) == language.name


@pytest.mark.django_db
def test_moderation_notification_model():
    notif = ModerationNotification.objects.create(objectid=1,
                                                  objecttype="notify",
                                                  text="Test Notification",
                                                  author="test"
                                                  )
    assert str(notif) == "notify id 1 (%s): Test Notification" % (notif.date)

    randomString = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=75))

    longer_notif = ModerationNotification.objects.create(objectid=1,
                                                         objecttype="notify",
                                                         text=randomString,
                                                         author="test"
                                                         )
    assert str(longer_notif) == "notify id 1 (%s): %s" % (longer_notif.date, randomString[:50])
