from django.db import models
from django.conf import settings

# Create your models here.

import json
import urllib2
import time
import os
import re
import datetime
import time

def print_timing(func):
    def wrapper(*args, **kw):
        t1 = time.time()
        res = func(*args, **kw)
        t2 = time.time()
        print '%0.3f ms: %s ( %s, %s )' % ((t2-t1)*1000.0, func.func_name, args, kw)
        return res
    return wrapper
    

class Project(object):
    def __init__(self, projectName = None):
        self.name = projectName
                
class Build(object):
    def __init__(self, buildjson = None, projectName = None):
        self.project = projectName

        if not buildjson:
            self.result = 'UNKNOWN'
            self.name = projectName
            self.projectName = projectName
            self.building = False
            self.duration = 0
            self.timeStamp = 0

        else:
            self.name = buildjson['fullDisplayName'].split(settings.HUDSON_TEST_NAME_PATTERN)[-1]
            self.building = buildjson['building']
            self.result = buildjson['result']
            if self.result == None and self.building:
                self.result = 'BUILDING'
            self.number = str(buildjson['number'])
            self.items = buildjson['changeSet']['items']
            self.scmKind = buildjson['changeSet']['kind']
            self.url = settings.HUDSON_URL+'/job/'+projectName+'/'+self.number+'/'
            self.duration = buildjson['duration'] / 1000
            self.timeStamp = buildjson['timestamp'] / 1000
            self.estimatedRemaining = 0
            self.description = buildjson['description']
            self.dateTimeStamp = datetime.datetime.fromtimestamp(self.timeStamp)
            self.smokeTests = {}
            self.baselineTests = {}
            self.projectTests = {}
            self.regressionTests = {}
            self.codeWatchTests = {}
            self.parent = None
            self.projectName = projectName
            self.builtOn= buildjson['builtOn']
            self.prior=None
            self.reRunCount=0

            actions = {}
            for action in buildjson['actions']:
                actions.update(action)
                
            self.failCount = actions.get('failCount', 0)
            self.totalCount = actions.get('totalCount', 0)
            
            if 'parameters' in actions:
                params = {}

                for p in actions['parameters']:
                   params[p['name']] = p

                if params.has_key('BUILDURL'):
                    buildurl = params['BUILDURL']
                    if 'number' in buildurl:
                        self.parent = str(buildurl['number'])
                    else:
                        self.parent = str(buildurl['value'].split('/')[-2])
                elif params.has_key('BUILD_NBR'):
                    self.parent = params['BUILD_NBR']['value']


            self.trigger = actions.get('causes')[0].get('shortDescription')


    @property
    def smoke_status(self):
        return test_status(self.smokeTests.values())

    @property
    def baseline_status(self):
        return test_status(self.baselineTests.values())

    @property
    def project_status(self):
        return test_status(self.projectTests.values())

    @property
    def regression_status(self):
        return test_status(self.regressionTests.values())

    @property
    def status(self):
        if self.building and self.reRunCount > 0:
            return 'REBUILDING'

        return self.building and 'BUILDING' or self.result

    @property
    def overall_status(self):
        return sorted([self.status, self.smoke_status, self.baseline_status, self.regression_status, self.project_status], cmp=compare_by_status)[0]

    @property
    def users(self):
        return [item['user'] for item in self.items]

    @property
    def msgs(self):
        return [item['msg'] for item in self.items]
 
    @property
    def display_users(self):
        return ', '.join([re.split(r'\||\/|-',user)[0] for user in self.users])

    @property
    def display_msgs(self):
        return '\n-------\n'.join([msg for msg in self.msgs])
        
    @property
    def elapsedTime(self):
        if self.timeStamp == 0:
            return 0
            
        if self.duration > 0:
            return self.duration
            
        return time.time() - self.timeStamp
        

    @property
    def totalElapsedTime(self):
        return sum([self.elapsedTime]+
            [max([test.elapsedTime for test in self.smokeTests.values()]+
            [test.elapsedTime for test in self.baselineTests.values()]+[0]+
            [test.elapsedTime for test in self.projectTests.values()]+[0]+
            [test.elapsedTime for test in self.regressionTests.values()]+[0])])

    @property
    def totalUnfinishedDuration(self):
        return sum([self.unfinishedDuration]+
            [max([test.unfinishedDuration for test in self.smokeTests.values()]+
            [test.unfinishedDuration for test in self.baselineTests.values()]+[0]+
            [test.unfinishedDuration for test in self.projectTests.values()]+[0]+
            [test.unfinishedDuration for test in self.regressionTests.values()]+[0])])
    
    @property
    def unfinishedDuration(self):
        if self.duration > 0 or self.timeStamp == 0:
            return 0

        return time.time() - self.timeStamp
                             
    @property
    def isSmokeStatusSame(self):
        firstTest = self.smokeTests.values()[0]
        result = all( (item.status == firstTest.status) for item in self.smokeTests.values())
        return result

    @property
    def isBaselineStatusSame(self):
        firstTest = self.baselineTests.values()[0]
        result = all( (item.status == firstTest.status) for item in self.baselineTests.values())
        return result

    @property
    def isProjectStatusSame(self):
        firstTest = self.projectTests.values()[0]
        result = all( (item.status == firstTest.status) for item in self.projectTests.values())
        return result

    @property
    def isRegressionStatusSame(self):
        firstTest = self.regressionTests.values()[0]
        result = all( (item.status == firstTest.status) for item in self.regressionTests.values())
        return result
        
    @property
    def failedSmokeTests(self):
        return [test for test in self.smokeTests.values() if test.result in ['FAILURE','UNSTABLE']]

    @property
    def failedCodeWatchTests(self):
        return [test for test in self.codeWatchTests.values() if test.result in ['WARNING','UNSTABLE']]


    @property
    def failedBaselineTests(self):
        return [test for test in self.baselineTests.values() if test.result in ['FAILURE','UNSTABLE']]

    @property
    def failedProjectTests(self):
        return [test for test in self.projectTests.values() if test.result in ['FAILURE','UNSTABLE']]

    @property
    def failedRegressionTests(self):
        return [test for test in self.regressionTests.values() if test.result in ['FAILURE','UNSTABLE']]

    @property
    def testCases(self):
        tests = []
        if self.status == 'UNKNOWN':
          return tests

        try:
            #tests = getTestData(get_data(self.url+"/testReport/api/json"),self.number)
            tests = getTestData(get_build(self.projectName, self.number, 'testReport' ),self.number)
        except urllib2.HTTPError:
            pass

        return tests

    @property
    def jenkinsUrl(self):
        if self.description and self.description.find('results_page:') > -1:
            return self.description.split('"')[1]
        else:
            return self.url

    @property
    def suiteInfoUrl(self):
        splitUrl = self.url.split("/")
        splitUrl.pop(-2)
        return "/".join(splitUrl) + "api/json"

    @property
    def causes(self):
        fName = settings.HUDSON_CAUSES_DIR + '/job/' + self.projectName + '/' + self.number + "/causes.html"
        try:
            f = open(fName, 'r')
            contents = f.read()
            f.close()
            return contents          
        except IOError:
	    return ""

status_order = ['FAILURE', 'UNSTABLE', 'REBUILDING', 'BUILDING', 'ABORTED', 'SUCCESS', 'UNKNOWN', None ]

def compare_by_status(r1, r2):
    return status_order.index(r1) - status_order.index(r2)

def compare_by_result(test1, test2):
    r1 = test1.result
    r2 = test2.result
    return compare_by_status(r1, r2)

def test_status(tests):
    if tests:
        tests_copy = list(tests)
        tests_copy.sort(cmp=compare_by_result)
        return tests_copy[0].status

def get_project_data(projectName):
    return get_data(settings.HUDSON_URL + '/job/' + projectName + '/api/json')

def get_data(url):
    return json.loads(urllib2.urlopen(url).read())

def get_build_info(projectName, build):
    if build is not None:
        return cleanup_cache(Build(build, projectName))

def cleanup_cache(build):
    filename = get_cache_filename(build.url)
    if build.building:
        try:
            os.remove(filename)
        except OSError:
            pass

    return build

def get_recent_builds(projectName, count):
    data = get_project_data(projectName)
    build_urls = sorted(data['builds'], key=lambda x: x['number'], reverse=True)[:count]
    return [build for build in [get_build_info(projectName, get_build(projectName,build_url['number'])) for build_url in build_urls] if build is not None]

def get_specific_build(projectName, build_number):
    return get_build_info(projectName, get_build(projectName, build_number))
    
def get_cache_filename(url):
    return '/tmp/jenkins_radiator/' + str(url.split('job/')[1]).strip('/').replace('/','_')

def get_build(projectName, number, suffix=""):
    url = settings.HUDSON_URL+'/job/'+projectName+'/'+str(number)+'/'+suffix
    filename = get_cache_filename(url)
    if os.path.exists(filename):
        try:
            return json.load(open(filename,'r'))
        except ValueError:
           os.remove(filename)
    try:
        build = get_data(url+'/api/json')

    except urllib2.HTTPError:
        return None

    if not os.path.exists('/tmp/jenkins_radiator'):
        os.mkdir('/tmp/jenkins_radiator')

    json.dump(build, open(filename,'w'))
    return build


def get_test_projects(data, build_type):
    jobs = data['jobs']
    testList = [job['name'] for job in jobs if job['name'].upper().startswith(build_type.upper() + '_TEST_')]
    return testList

def get_code_watch_projects(data, build_type):
    jobs = data['jobs']
    watchList = [job['name'] for job in jobs if job['name'].upper().startswith(build_type.upper() + '_CODE_WATCH_')]
    return watchList

def flatten(x):
    cases = []
    cases.extend(x)
    return cases

def get_codeWatchStatus(buildUrl, buildStatus):
    try:
        artifactsJson = json.loads(urllib2.urlopen(buildUrl + "api/json").read())["artifacts"]
        codeWatch_status = "ABORTED"
        if buildStatus == "SUCCESS" :
            codeWatch_status = "WARNING"
            for artifactJson in artifactsJson:
                pageDataUrl = buildUrl + "artifact/" + artifactJson["relativePath"]
                codeWatchJasonData = json.loads(urllib2.urlopen(pageDataUrl).read())
                build_info = codeWatchJasonData["build_info"]
                if build_info["status"] == "pass" :
                    codeWatch_status = "SUCCESS"
        return codeWatch_status
    except urllib2.HTTPError:
        return None


class TestData(object):
    def __init__(self, case, runNumber):
        self.status = case['status']
        self.duration = case['duration']
        self.name = case['className']+"."+case['name']
        self.runNumber = runNumber


def getTestData(jsonData,runNumber):
    tests = []
    if jsonData:
        if jsonData.has_key('childReports'):
            try:
                jsonData = jsonData['childReports'][0]['result']
            except IndexError:
                return tests

        suites = flatten(s['cases'] for s in jsonData['suites'])
        for suite in suites:
            for case in suite:
                tests.extend([TestData(case,runNumber)])

    return tests
