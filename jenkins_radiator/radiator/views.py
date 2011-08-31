from django.shortcuts import render_to_response as render
from django.conf import settings
import models
import re

markup_constants = {"up_arrow": u"\u25B2",
                    "down_arrow": u"\u25BC"}

# Create your views here.
def avg(lst):
    return sum(lst) / (1.0 * len(lst))


def get_radiator(request, build_list):
    const = markup_constants
    buildCount = request.GET.get('builds', settings.HUDSON_BUILD_COUNT)
    build_types = [build_row.split(',') for build_row in build_list.split('|')]
    columnSize = 100 / len(build_types[0])
    return render('radiator/builds.html', locals())


def get_builds(request, build_type):
    const = markup_constants
    count = int(request.GET.get('builds', settings.HUDSON_BUILD_COUNT))
    builds = models.get_recent_builds(build_type + settings.HUDSON_BUILD_NAME_PATTERN, count)
    buildDict = lookupTests(build_type, count, builds)

    if len(builds) > 1:
        avgTime = avg([build.totalElapsedTime for build in builds if build.overall_status != 'BUILDING'])
        for build in builds:
            if build.totalUnfinishedDuration > 0:
                build.estimatedRemaining = avgTime - build.totalUnfinishedDuration

    return render('radiator/builds_table.html', locals())


def get_build_info(request, build_type, build_number):
    const = markup_constants
    build = models.get_specific_build(build_type + '_Build', build_number)
    buildDict = lookupTests(build_type, 20, [build])
    return render('radiator/build_detail.html', locals())


def lookupTests(build_type, count, builds):
    project = models.Project(build_type)

    testProjects = models.get_test_projects(models.get_data(settings.HUDSON_URL + '/api/json?tree=jobs[name]'),
                                            build_type)
    testProjects = [proj for proj in testProjects if not settings.HUDSON_TEST_IGNORE_REGEX.findall(proj)]
    project.smokeProjects = [proj for proj in testProjects if settings.HUDSON_SMOKE_NAME_REGEX.findall(proj)]
    project.baselineProjects = [proj for proj in testProjects if settings.HUDSON_BASELINE_NAME_REGEX.findall(proj)]
    project.otherProjects = [proj for proj in testProjects if not settings.HUDSON_SMOKE_NAME_REGEX.findall(proj)]
    project.otherProjects = [proj for proj in project.otherProjects if
                             not settings.HUDSON_BASELINE_NAME_REGEX.findall(proj)]

    project.perfProjects = models.get_performance_projects(
        models.get_data(settings.HUDSON_URL + '/api/json?tree=jobs[name]'), build_type)

    project.codeWatchProjects = models.get_code_watch_projects(
        models.get_data(settings.HUDSON_URL + '/api/json?tree=jobs[name]'), build_type)

    buildDict = dict((build.number, build) for build in builds)

    smokeBuilds = []
    for testName in project.smokeProjects:
        smokeBuilds.extend(models.get_recent_builds(testName, count))

    baselineBuilds = []
    for testName in project.baselineProjects:
        baselineBuilds.extend(models.get_recent_builds(testName, count))

    regressionBuilds = []
    for testName in project.otherProjects:
        regressionBuilds.extend(models.get_recent_builds(testName, count))

    perfBuilds = []
    for testName in project.perfProjects:
        perfBuilds.extend(models.get_recent_builds(testName, count))

    codeWatchBuilds = []
    for testName in project.codeWatchProjects:
        codeWatchBuilds.extend(models.get_recent_builds(testName, count))

    for test in smokeBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.smokeTests or int(test.number) > int(parent.smokeTests[test.project].number):
                parent.smokeTests[test.project] = test

    for test in baselineBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.baselineTests or int(test.number) > int(
                parent.baselineTests[test.project].number):
                parent.baselineTests[test.project] = test

    for test in regressionBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.regressionTests or int(test.number) > int(
                parent.regressionTests[test.project].number):
                parent.regressionTests[test.project] = test

    for test in perfBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.perfTests or int(test.number) > int(parent.perfTests[test.project].number):
                parent.perfTests[test.project] = test

    for test in codeWatchBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.codeWatchTests or int(test.number) > int(parent.codeWatchTests[test.project].number):
                parent.codeWatchTests[test.project] = test

    for build in builds:
        for smoke in project.smokeProjects:
            if smoke not in build.smokeTests:
                build.smokeTests[smoke] = models.Build(projectName=smoke)

        for baseline in project.baselineProjects:
            if baseline not in build.baselineTests:
                build.baselineTests[smoke] = models.Build(projectName=baseline)

        for perf in project.perfProjects:
            if perf not in build.perfTests:
                build.perfTests[perf] = models.Build(projectName=perf)

        for watch in project.codeWatchProjects:
            if watch not in build.codeWatchTests:
                build.codeWatchTests[watch] = models.Build(projectName=watch)

            for other in project.otherProjects:
                if other not in build.regressionTests:
                    build.regressionTests[other] = models.Build(projectName=other)

        # Find prior build with perf data

        for perfProject in project.perfProjects:
            lastSuccessfulBuild = None
            for build in reversed(builds):
                if build.perfTests[perfProject].result == "SUCCESS":
                    build.perfTests[perfProject].prior = lastSuccessfulBuild
                    lastSuccessfulBuild = build.perfTests[perfProject]

        for perfBuild in perfBuilds:
            perfBuild.pagePerfs = models.create_pagePerfs(perfBuild.url)

        for codeWatchBuild in codeWatchBuilds:
            codeWatchBuild.codeWatchStatus = models.get_codeWatchStatus(codeWatchBuild.url, codeWatchBuild.status)

        for perfBuild in perfBuilds:
            perfBuild.pagePerfDeltas = []
            for pageName, pagePerf in perfBuild.pagePerfs.iteritems():
                if perfBuild.prior:
                    if perfBuild.prior.pagePerfs.has_key(pageName):
                        priorPagePerf = perfBuild.prior.pagePerfs[pageName]
                        perfBuild.pagePerfDeltas.append(models.PagePerformanceDelta(pagePerf, priorPagePerf))
                else:
                    perfBuild.pagePerfDeltas.append(models.PagePerformanceDelta(pagePerf))

        return buildDict

    def get_project_report(request, build_type):
        count = int(request.GET.get('builds', settings.HUDSON_BUILD_COUNT))
        builds = models.get_recent_builds(build_type + settings.HUDSON_BUILD_NAME_PATTERN, count)
        buildDict = lookupTests(build_type, count, builds)
        caseDict = {}
        tests = []
        for build in sorted(buildDict.values(), key=lambda build: build.number, reverse=True):
            tests.append(build)
            compile_project_test_cases(build, caseDict)

        summary = summarize_test_cases(caseDict)
        return render('radiator/test_report.html', locals())

    def compile_project_test_cases( build, allCases ):
        for test in build.smokeTests.values() + build.baselineTests.values() + build.regressionTests.values():
            if test.testCases:
                for case in test.testCases:
                    errorCount, casesByBuildNbr = allCases.get(case.name, (0, {}))
                    casesByBuildNbr[build.number] = case
                    if case.status in ['FAILED', 'REGRESSION']:
                        errorCount = errorCount + 1
                    allCases.update({case.name: (errorCount, casesByBuildNbr)})
        return allCases


    def get_test_report(request, test_name):
        count = int(request.GET.get('builds', settings.HUDSON_BUILD_COUNT))
        tests = models.get_recent_builds(test_name, count)
        caseDict = compile_test_cases(tests, test_name)
        summary = summarize_test_cases(caseDict)

        return render('radiator/test_report.html', locals())


    def compile_test_cases(tests, test_name):
        allCases = {}
        for test in tests:
            if test.testCases:
                for case in test.testCases:
                    errorCount, casesByRun = allCases.get(case.name, (0, {}))
                    casesByRun[case.runNumber] = case
                    if case.status in ['FAILED', 'REGRESSION']:
                        errorCount = errorCount + 1
                    allCases.update({case.name: (errorCount, casesByRun)})
        return allCases

    def summarize_test_cases(caseDict):
        summary = []
        for k, v in caseDict.iteritems():
            triple = (k, v[0], v[1])
            summary.append(triple)

        return sorted(summary, key=lambda c: c[1], reverse=True)

