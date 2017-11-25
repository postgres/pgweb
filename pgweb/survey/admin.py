from django.contrib import admin
from models import Survey, SurveyLock, SurveyAnswer

class SurveyAdmin(admin.ModelAdmin):
	list_display = ('question','posted','current',)
	ordering = ('-posted',)

class SurveyAnswerAdmin(admin.ModelAdmin):
	list_display = ('survey','tot1','tot2','tot3','tot4','tot5','tot6','tot7','tot8')
	ordering = ('-survey__posted',)

admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveyLock)
admin.site.register(SurveyAnswer, SurveyAnswerAdmin)
