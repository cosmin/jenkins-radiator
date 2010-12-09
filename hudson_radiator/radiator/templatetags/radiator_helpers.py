from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
@stringfilter
def colorize_status(value):
    if value == 'FAILURE':
        ret = "<font color='red'>" + value + "</font>"
    elif value == 'SUCCESS':
        ret = "<font color='00FF00'>" + value + "</font>"
    elif value == 'UNSTABLE':
        ret = "<font color='orange'>" + value + "</font>"
    elif value == 'ABORTED':
        ret = "<font color='999999'>" + value + "</font>"
    elif value == 'BUILDING':
        ret = "<font color='yellow'>" + value + "</font>"
    else:
        ret = value
    return mark_safe(ret)

@register.filter
@stringfilter
def table_color(value):
    if value == 'FAILURE':
        return "#480000"

    if value == 'UNSTABLE':
        return "#484800"

    if value == 'SUCCESS':
        return "#004800"

    if value == 'ABORTED':
        return "#404040"

    return "#202020"


@register.filter
@stringfilter
def progress_bar(runningTime, avgTime):
    bar = '<table id="progress-bar" ><tbody><tr><td style="width:'
    bar += int(runningTime / avgTime);
    bar += '%;" class="progess-bar-done"></td>'
    bar += '<td style="width:'
    bar += 100 - int(runningTIme / avgTime);
    bar += '%;" class="progress-bar-left"></td></tr></tbody></tr>'
    return bar

@register.filter
@stringfilter
def firstWord(value):
  return value.split(' ')[0]
