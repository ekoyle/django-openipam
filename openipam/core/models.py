# monkey-pathching django admin
from django.conf import settings
from django.contrib.admin import widgets
from django import forms
from django.db import models
from admin_tools.menu import items


TYPE_CHOICES = (
    ('feature', 'Feature',),
    ('bug', 'Bug',),
    ('comment', 'Comment',),
)


class FeatureRequest(models.Model):
    comment = models.TextField('Comment Detail')
    type = models.CharField('Request Type', max_length=255, choices=TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    submitted = models.DateTimeField('Date Submitted', auto_now_add=True)

    def __unicode__(self):
        return '%s - %s' % (self.type, self.comment)

    class Meta:
        db_table = 'feature_requests'
        ordering = ('-submitted',)


class FilteredSelectMultiple(forms.SelectMultiple):
    """
        removing 2 select fields widget
    """
    def __init__(self, verbose_name, is_stacked, attrs=None, choices=[]):
        super(FilteredSelectMultiple, self).__init__(attrs, choices)
widgets.FilteredSelectMultiple = FilteredSelectMultiple

# patching admintools menu item
# addming icon argument to base MenuItem class
items.MenuItem.icon = None


# pathing AdminDateInput
class ATBAdminDateWidget(forms.DateInput):
    def __init__(self, attrs=None, format=None):
        final_attrs = {'class': 'vDateField', 'size': '10'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(ATBAdminDateWidget, self).__init__(attrs=final_attrs, format=format)

widgets.AdminDateWidget.media = forms.Media()
