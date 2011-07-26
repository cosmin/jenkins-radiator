from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from datetime import datetime

import re
from jenkins_radiator.radiator.models import compare_by_result

up_arrow = u"\u25B2"
down_arrow = u"\u25BC"

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
def sortedByName(lst):
    return sorted(lst, key=lambda Build: Build.name)

@register.filter
def sortedByIndex(lst):
    return sorted(lst, key=lambda PagePerformanceDelta: PagePerformanceDelta.index)

@register.filter
def sortedByStatus(lst):
    lst.sort( cmp=compare_by_result,reverse=True)
    return lst
    
@register.filter
def filterStatus(tests, status):
    return [test for test in tests if test.result not in status]

@register.filter
def cases(caseDict, name):
    cases = caseDict[name]
    return cases[1]

@register.filter
def testCaseState(cases,runNumber):
    if runNumber in cases:
        case = cases[runNumber]
        if case.status == 'FIXED':
            return 'PASSED'
        if case.status == 'REGRESSION':
            return 'FAILED'
        return case.status
    return ''

@register.filter
@stringfilter
def shorten(value, length=1):
    return value[0:length]

@register.filter
@stringfilter
def dot2slash(value):
    return value.replace('.','/')

@register.filter
def formatForLabel(pagePerf):
    scoreIndicator = ""
    if pagePerf.scoreDelta > 0:
        scoreIndicator = up_arrow
    if pagePerf.scoreDelta < 0:
        scoreIndicator = down_arrow

    totalRequestsIndicator = ""
    if pagePerf.totalRequestsDelta > 0:
        totalRequestsIndicator = up_arrow
    if pagePerf.totalRequestsDelta < 0:
        totalRequestsIndicator = down_arrow

    totalKilobytesIndicator = ""
    if pagePerf.totalKilobytesDelta > 0:
        totalKilobytesIndicator = up_arrow
    if pagePerf.totalKilobytesDelta < 0:
        totalKilobytesIndicator = down_arrow

    return u"{0} \nTotal Requests: {1} {2} \nPage Weight: {3}KB {4}"\
        .format(pagePerf.name, pagePerf.totalRequests, totalRequestsIndicator,  pagePerf.totalKilobytes, totalKilobytesIndicator)
    

@register.filter
def wordbreak (string, arg):
    search = '([^ ]{' + arg + '})'
    t = datetime.now()
    wbr = t.strftime("%A%d%B%Y%f") + 'wbr_here' + t.strftime("%A%d%B%Y%f")
    saferesult = conditional_escape(re.sub( search, '\\1' + wbr, string ))
    result = saferesult.replace(wbr,'&shy;')
    return mark_safe(result)
    
@register.filter
def format_seconds_to_mmss(seconds):
    if seconds == '':
            seconds = 0
            
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i" % (minutes, seconds)