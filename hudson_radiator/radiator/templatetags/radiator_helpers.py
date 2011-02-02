from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import re
from hudson_radiator.radiator.models import compare_by_status

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
def transformTestStatus(value):
    if value == 'FAILURE':
        return "FAILED TO COMPLETE"

    if value == 'UNSTABLE':
        return "TESTS FAILED"

    if value == 'SUCCESS':
        return "Passed"

    if value == 'BUILDING':
        return "Running ..."

    if value == 'UNKNOWN':
        return "Not run (yet)"
    return value


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
  return re.split('\||\/|-',value)[0]

@register.filter
def plural(a):
    if len(a) == 1:
        return ''
        
    return 's'

@register.filter
def sortedByStatus(lst):
    lst.sort( cmp=compare_by_status,reverse=True)
    return lst
    
@register.filter
def filterStatus(tests, status):
    return [test for test in tests if test.result not in status]