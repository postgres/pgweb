from django.contrib import admin
from django import forms

from pgweb.util.admin import PgwebAdmin
from pgweb.core.models import OrganisationEmail
from .models import NewsArticle, NewsTag


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
    exclude = ('modstate', 'firstmoderator', )
    form = NewsArticleAdminForm


class NewsTagAdmin(PgwebAdmin):
    list_display = ('urlname', 'name', 'description')
    filter_horizontal = ('allowed_orgs', )


admin.site.register(NewsArticle, NewsArticleAdmin)
admin.site.register(NewsTag, NewsTagAdmin)
