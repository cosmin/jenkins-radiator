from django.db import models
from django.conf import settings

# Create your models here.

import json
import urllib2
import time
import os
import re
import datetime

class Build(object):
    def __init__(self, buildjson, projectName = None):
        self.name = buildjson['fullDisplayName'].split(settings.HUDSON_TEST_NAME_PATTERN)[-1]
        self.project = projectName
        self.building = buildjson['building']

        self.result = buildjson['result']
        if self.result == None and self.building:
            self.result = 'BUILDING'
       
        self.number = str(buildjson['number'])
        self.items = buildjson['changeSet']['items']
        self.url = settings.HUDSON_URL+'/job/'+projectName+'/'+self.number+'/'
        self.duration = buildjson['duration'] / 1000
        self.timeStamp = buildjson['timestamp'] / 1000
        self.dateTimeStamp = datetime.datetime.fromtimestamp(self.timeStamp)
        self.smokeTests = {}
        self.regressionTests = {}
        self.parent = None

        actions = {}
        for action in buildjson['actions']:
            actions.update(action)

        if 'parameters' in actions:
            params = {}

            for p in actions['parameters']:
               params[p['name']] = p

            buildurl = params['BUILDURL']
            if 'number' in buildurl:
               self.parent = str(buildurl['number'])
            else:
               self.parent = str(buildurl['value'].split('/')[-2])

    @property
    def smoke_status(self):
        return test_status(self.smokeTests.values())

    @property
    def regression_status(self):
        return test_status(self.regressionTests.values())

    @property
    def status(self):
        return self.building and 'BUILDING' or self.result

    @property
    def revisions(self):
        return [item['revision'] for item in self.items]

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
    def runningTime(self):
        if self.duration > 0:
            return ''
        
        return time.time() - self.timeStamp

status_order = ['FAILURE', 'UNSTABLE', 'ABORTED', 'BUILDING', 'SUCCESS']

def compare_by_status(test1, test2):
    r1 = test1.result
    r2 = test2.result
    return status_order.index(r1) - status_order.index(r2)

def test_status(tests):
    if tests:
        tests_copy = list(tests)
        tests_copy.sort(cmp=compare_by_status)
        return tests_copy[0].result

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

def get_first_20(projectName):
    data = get_project_data(projectName)
    build_urls = sorted(data['builds'], key=lambda x: x['number'], reverse=True)[:10]
    return [build for build in [get_build_info(projectName, get_build(projectName,build_url['number'])) for build_url in build_urls] if build is not None]

def get_cache_filename(url):
    return '/tmp/hudson_radiator/' + str(url.split('job/')[1]).strip('/').replace('/','_')
    
def get_build(projectName, number):
    url = settings.HUDSON_URL+'/job/'+projectName+'/'+str(number)+'/'
    filename = get_cache_filename(url)
    if os.path.exists(filename):
        try:
            return json.load(open(filename,'r'))
        except ValueError:
           os.remove(filename)
   
    try:
        build = get_data(url+'api/json')
    
    except urllib2.HTTPError:
        return None

    if not os.path.exists('/tmp/hudson_radiator'):
        os.mkdir('/tmp/hudson_radiator');

    json.dump(build, open(filename,'w'))
    return build


def get_test_projects(data, build_type):
    jobs = data['jobs']
    return [job['name'] for job in jobs if job['name'].upper().startswith(build_type.upper() + '_TEST_')]

