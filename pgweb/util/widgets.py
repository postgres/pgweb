from django.forms.widgets import Widget


class TemplateRenderWidget(Widget):
    def __init__(self, *args, **kwargs):
        self.template_name = kwargs.pop('template')
        self.templatecontext = kwargs.pop('context')

        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        return self.templatecontext
