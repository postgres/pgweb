from django.contrib import admin
from django import forms

from pgweb.util.admin import PgwebAdmin
from pgweb.util.moderation import ModerationState
from pgweb.core.models import OrganisationEmail
from .models import NewsArticle, NewsTag, PinnedNewsArticle

from datetime import datetime, timedelta


class NewsArticleAdminForm(forms.ModelForm):
    model = NewsArticle

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['email'].queryset = OrganisationEmail.objects.filter(org=self.instance.org, confirmed=True)


class NewsArticleAdmin(PgwebAdmin):
    list_display = ('title', 'org', 'date', 'modstate', 'permanenturl')
    list_filter = ('modstate', )
    filter_horizontal = ('tags', )
    search_fields = ('content', 'title', )
    exclude = ('modstate', 'firstmoderator', 'ispinned', )
    form = NewsArticleAdminForm


class PinnedNewsArticleAdminForm(forms.ModelForm):
    model = PinnedNewsArticle

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pinnedarticle'].queryset = NewsArticle.objects.filter(modstate=ModerationState.APPROVED, date__gt=datetime.now() - timedelta(days=365)).order_by('-date')
        self.fields['pinnedarticle'].widget.can_delete_related = False
        self.fields['pinnedarticle'].widget.can_add_related = False


class PinnedNewsArticleAdmin(admin.ModelAdmin):
    exclude = ('pinnedtoproviders', )
    form = PinnedNewsArticleAdminForm

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NewsTagAdmin(PgwebAdmin):
    list_display = ('urlname', 'name', 'description')
    filter_horizontal = ('allowed_orgs', )


admin.site.register(NewsArticle, NewsArticleAdmin)
admin.site.register(NewsTag, NewsTagAdmin)
admin.site.register(PinnedNewsArticle, PinnedNewsArticleAdmin)
