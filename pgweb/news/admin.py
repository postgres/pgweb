from django.contrib import admin

from pgweb.util.admin import PgwebAdmin
from .models import NewsArticle, NewsTag


class NewsArticleAdmin(PgwebAdmin):
    list_display = ('title', 'org', 'date', 'approved', )
    list_filter = ('approved', )
    filter_horizontal = ('tags', )
    search_fields = ('content', 'title', )
    change_form_template = 'admin/news/newsarticle/change_form.html'

    def change_view(self, request, object_id, extra_context=None):
        newsarticle = NewsArticle.objects.get(pk=object_id)
        my_context = {
            'latest': NewsArticle.objects.filter(org=newsarticle.org)[:10]
        }
        return super(NewsArticleAdmin, self).change_view(request, object_id, extra_context=my_context)


class NewsTagAdmin(PgwebAdmin):
    list_display = ('urlname', 'name', 'description')
    filter_horizontal = ('allowed_orgs', )


admin.site.register(NewsArticle, NewsArticleAdmin)
admin.site.register(NewsTag, NewsTagAdmin)
