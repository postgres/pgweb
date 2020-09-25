from django.contrib import admin
from django import forms
from django.template.defaultfilters import slugify

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
    list_display = ('title', 'org', 'date', 'modstate', 'posturl')
    list_filter = ('modstate', )
    filter_horizontal = ('tags', )
    search_fields = ('content', 'title', )
    exclude = ('modstate', 'firstmoderator', )
    form = NewsArticleAdminForm

    def posturl(self, obj):
        return '/about/news/{}-{}/'.format(slugify(obj.title), obj.id)


class NewsTagAdmin(PgwebAdmin):
    list_display = ('urlname', 'name', 'description')
    filter_horizontal = ('allowed_orgs', )


admin.site.register(NewsArticle, NewsArticleAdmin)
admin.site.register(NewsTag, NewsTagAdmin)
