from django.db import models
from django.conf import settings

# Create your models here.

import json
import urllib2
import time
import os

class Build(object):
    def __init__(self, buildjson):
        self.name = buildjson['fullDisplayName'].split(settings.HUDSON_TEST_NAME_PATTERN)[-1]
        self.building = buildjson['building']

        self.result = buildjson['result']
        if self.result == None and self.building:
            self.result = 'BUILDING'
       
        self.number = str(buildjson['number'])
        self.items = buildjson['changeSet']['items']
        self.url = buildjson['url']
        self.duration = buildjson['duration'] / 1000
        self.timeStamp = buildjson['timestamp'] / 1000
        self.smokeTests = []
        self.regressionTests = []
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
        return test_status(self.smokeTests)

    @property
    def regression_status(self):
        return test_status(self.regressionTests)

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
        return ', '.join([user.split(' ')[0] for user in self.users])

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

def get_data(url):
    return json.loads(urllib2.urlopen(url).read())

def get_build_info(build):
    if build is not None:
        return cleanup_cache(Build(build))

def cleanup_cache(build):
    filename = get_cache_filename(build.url)
    if build.building:
        os.remove(filename)

    return build

def get_first_20(data):
    build_urls = sorted(data['builds'], key=lambda x: x['number'], reverse=True)[:20]
#    return [get_build_info(json.loads(urllib2.urlopen(build_url['url'] + 'api/json').read())) for build_url in build_urls]
    return [build for build in [get_build_info(get_build(build_url['url'])) for build_url in build_urls] if build is not None]

def get_cache_filename(url):
    return '/tmp/hudson_radiator/' + str(url.split('job/')[1]).strip('/').replace('/','_')
    
def get_build(url):
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

