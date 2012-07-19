from django.shortcuts import render_to_response as render
from django.conf import settings
import models
import re
import socket
import time
import threading
import sys, traceback
import atexit
markup_constants = {"up_arrow": u"\u25B2",
                    "down_arrow": u"\u25BC"}
topicThread=None
ircTopic = ""
ircMsg = ""

# Create your views here.
def avg(lst):
    return sum(lst) / (1.0 * len(lst))


def get_radiator(request, build_list):
    ircTopicBuild = settings.IRC_TOPIC_BUILD_NAME
    const = markup_constants
    buildCount = request.GET.get('builds', settings.HUDSON_BUILD_COUNT)
    build_types = [build_row.split(',') for build_row in build_list.split('|')]
    if hasattr(settings,'IRC_HOST'):
        build_topic = irc_channel_topic()
        build_msg = irc_channel_msg()

    columnSize = 100 / len(build_types[0])
    return render('radiator/builds.html', locals())

def get_stats(request, build_type):
    buildCount = int(request.GET.get('builds', settings.HUDSON_BUILD_COUNT))
    returnURL = request.GET.get('returnURL')
    if returnURL and returnURL.find("?builds=") != -1:
        buildCount = int(returnURL[returnURL.index("?builds=") + 8:len(returnURL)])

    builds = models.get_recent_builds(build_type + settings.HUDSON_BUILD_NAME_PATTERN, buildCount)
    if len(builds) > 1:
        buildTimes = [build.totalElapsedTime for build in builds if build.result != 'BUILDING']
        buildNums = len(buildTimes)
        buildTimes.remove(min(buildTimes))
        buildTimes.remove(max(buildTimes))
        minTime = min(buildTimes)
        avgTime = avg(buildTimes)
        maxTime = max(buildTimes)
        buildSuccesses = len([build.result for build in builds if build.result == 'SUCCESS'])
        buildFailures = buildNums - buildSuccesses
        if buildNums > 0:
            buildSuccessPercent = round((float(buildSuccesses) / float(buildNums)) * 100, 2)
            buildFailurePercent = 100 - buildSuccessPercent

    testProjects = models.get_test_projects(models.get_data(settings.HUDSON_URL + '/api/json?tree=jobs[name]'), build_type)
    testProjects = [proj for proj in testProjects if not settings.HUDSON_TEST_IGNORE_REGEX.findall(proj)]

    testBuilds = {}

    for testName in testProjects:
        tests = models.get_recent_builds(testName, buildCount)
        testTimes = [test.totalElapsedTime for test in tests if test.result != 'BUILDING']
        testNums = len(testTimes)
        testTimes.remove(min(testTimes))
        testTimes.remove(max(testTimes))
        testSuccesses = len([test.result for test in tests if test.result == 'SUCCESS'])
        testFailures = testNums - testSuccesses
        if testNums > 0:
            testSuccessPercent = round((float(testSuccesses) / float(testNums)) * 100, 2)
            testFailurePercent = 100 - testSuccessPercent

        if testNums > 1:
            testNameStripped = testName
            if testName.find("Test_") != -1:
                testNameStripped = testName[testName.index("Test_") + 5:len(testName)]

            testBuilds[testNameStripped]=[min(testTimes), avg(testTimes), max(testTimes), testSuccesses, testSuccessPercent, testFailures, testFailurePercent, testNums, tests[-1].totalCount]

    return render('radiator/stats_page.html', locals())

def get_state(request, build_type):
    const = markup_constants
    count = int(request.GET.get('builds', settings.HUDSON_BUILD_COUNT))
    builds = models.get_recent_builds(build_type + settings.HUDSON_BUILD_NAME_PATTERN, count)
    buildDict = lookupTests(build_type, count, builds)
    state = "UNKNOWN"
    buildingCount = 0
    for build in builds:
        state = build.overall_status
 
        if state == "BUILDING":
            buildingCount += 1
            if buildingCount >= settings.HUDSON_MAXIMUM_CONCURRENT_BUILDS:
                state = "BUSY"
                break

        if state != "BUILDING" and state != "ABORTED":
            break

    return render('radiator/state.html', locals())

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
    project.baselineProjects = [proj for proj in project.baselineProjects if not settings.HUDSON_PROJECT_NAME_REGEX.findall(proj)]
    
    project.projectSuiteProjects = [proj for proj in testProjects if settings.HUDSON_PROJECT_NAME_REGEX.findall(proj)]
    
    project.otherProjects = [proj for proj in testProjects if not settings.HUDSON_SMOKE_NAME_REGEX.findall(proj)]
    project.otherProjects = [proj for proj in project.otherProjects if
                             not settings.HUDSON_PROJECT_NAME_REGEX.findall(proj)]

    project.codeWatchProjects = models.get_code_watch_projects(
        models.get_data(settings.HUDSON_URL + '/api/json?tree=jobs[name]'), build_type)

    buildDict = dict((build.number, build) for build in builds)

    smokeBuilds = []
    for testName in project.smokeProjects:
        smokeBuilds.extend(models.get_recent_builds(testName, count))

    baselineBuilds = []
    for testName in project.baselineProjects:
        baselineBuilds.extend(models.get_recent_builds(testName, count))
   
    projectBuilds = []
    for testName in project.projectSuiteProjects:
        projectBuilds.extend(models.get_recent_builds(testName, count))
 
    regressionBuilds = []
    for testName in project.otherProjects:
        regressionBuilds.extend(models.get_recent_builds(testName, count))

    codeWatchBuilds = []
    for testName in project.codeWatchProjects:
        codeWatchBuilds.extend(models.get_recent_builds(testName, count))

    for test in smokeBuilds:
        myParent = test.parent
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.smokeTests:
                parent.smokeTests[test.project] = test
            else:
                if int(test.number) > int(parent.smokeTests[test.project].number):
                    test.reRunCount += parent.smokeTests[test.project].reRunCount
                    parent.smokeTests[test.project] = test
                else:
                    parent.smokeTests[test.project].reRunCount += 1

    for test in baselineBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.baselineTests:
                parent.baselineTests[test.project] = test
            else:
                if int(test.number) > int(parent.baselineTests[test.project].number):
                    test.reRunCount += parent.baselineTests[test.project].reRunCount
                    parent.baselineTests[test.project] = test
                else:
                    parent.baselineTests[test.project].reRunCount += 1

    for test in projectBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.projectTests:
                parent.projectTests[test.project] = test
            else:
                if int(test.number) > int(parent.projectTests[test.project].number):
                    test.reRunCount += parent.projectTests[test.project].reRunCount
                    parent.projectTests[test.project] = test
                else:
                    parent.projectTests[test.project].reRunCount += 1

    for test in regressionBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.regressionTests:
                parent.regressionTests[test.project] = test
            else:
                if int(test.number) > int(parent.regressionTests[test.project].number):
                    test.reRunCount += parent.regressionTests[test.project].reRunCount
                    parent.regressionTests[test.project] = test
                else:
                    parent.regressionTests[test.project].reRunCount += 1

    for test in codeWatchBuilds:
        parent = buildDict.get(test.parent)
        if parent is not None:
            if test.project not in parent.codeWatchTests or int(test.number) > int( parent.codeWatchTests[test.project].number):
                parent.codeWatchTests[test.project] = test

    for build in builds:
        for smoke in project.smokeProjects:
            if smoke not in build.smokeTests:
                build.smokeTests[smoke] = models.Build(projectName=smoke)

        for baseline in project.baselineProjects:
            if baseline not in build.baselineTests:
                build.baselineTests[baseline] = models.Build(projectName=baseline)
       
        for xproject in project.projectSuiteProjects:
            if xproject not in build.projectTests:
                build.projectTests[project] = models.Build(projectName=project)

        for watch in project.codeWatchProjects:
            if watch not in build.codeWatchTests:
                build.codeWatchTests[watch] = models.Build(projectName=watch)

            for other in project.otherProjects:
                if other not in build.regressionTests:
                    build.regressionTests[other] = models.Build(projectName=other)

        for codeWatchBuild in codeWatchBuilds:
            codeWatchBuild.codeWatchStatus = models.get_codeWatchStatus(codeWatchBuild.url, codeWatchBuild.status)

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

    tests.sort(key=lambda build: build.number, reverse=True)
    summary = summarize_test_cases(caseDict)
    return render('radiator/test_report.html', locals())

def compile_project_test_cases( build, allCases ):
    for test in build.smokeTests.values() + build.baselineTests.values() + build.regressionTests.values() + build.projectTests.values():
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

def irc_channel_msg():
  global topicThread
  global ircMsg

  ensureTopicThreadExists()

  if ircMsg == "" :
     topicThread.refreshMsg()

  return ircMsg

def irc_channel_topic(): 
  global topicThread
  global ircTopic

  ensureTopicThreadExists()

  if ircTopic == "" :
     topicThread.refreshTopic()

  return ircTopic

def ensureTopicThreadExists():
  global topicThread
  if topicThread == None :
     ircTopicThreadCreate()
  elif not topicThread.isRunning :
     ircTopicThreadCreate()


def ircTopicThreadCreate():
    global settings
    global topicThread
    topicThread = IRCTopicThread()
    topicThread.start()
    time.sleep(settings.IRC_TOPIC_POLL_INTERVAL_SECONDS_FLOAT)

class IRCTopicThread(threading.Thread) :
   global settings
   isRunning=False
   try:
     __ircSocket   = None
     __ircErrorMsg = settings.IRC_TOPIC_ERROR_MSG
     __eol      = '\n'
     __status   = 0
     __buf      = ""
     __rcvSize  = 2048
     __nickCmd  = "NICK %s\r\n" % settings.IRC_NICK
     __userCmd  = "USER %s %s greetings earthlings! :  %s\r\n" % (settings.IRC_IDENT, settings.IRC_HOST, settings.IRC_REALNAME)
     __joinCmd  = "JOIN %s \r\n" % settings.IRC_CHAN
     __topicCmd = "TOPIC  %s\r\n" % settings.IRC_CHAN
     __quitCmd  = "QUIT\r\n"
     __pauseAmt = settings.IRC_TOPIC_POLL_INTERVAL_SECONDS_FLOAT
     __topicBoundary = settings.IRC_CHAN
     __msgBoundary   = settings.IRC_NICK
   except Exception as e :
     print 'Missing settings for IRC topic support... carry on!'
     print "Exception : {0}\r\n".format(e)
     exc_type, exc_value, exc_traceback = sys.exc_info()
     traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)

   def __init__(self) :
     threading.Thread.__init__(self)
     try:    
        self.__ircSocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__ircSocket.connect((settings.IRC_HOST, settings.IRC_PORT))
        self.__ircSocket.settimeout(self.__pauseAmt)
     
        if self.__send_irc_cmd(self.__nickCmd) :
           self.__recv_irc_resp(None,None)
        else :
           self.__ircSocket.close
           self.__ircSocket = None
           return

        if self.__send_irc_cmd(self.__userCmd) :
           self.__recv_irc_resp(re.compile(settings.IRC_RSP_USER),None)
        else :
           self.__ircSocket.close
           self.__ircSocket = None
           return

        if self.__send_irc_cmd(self.__joinCmd) : 
           self.__recv_irc_resp(re.compile(settings.IRC_RSP_JOIN),None)
        else :
           __ircSocket.close
           __ircSocket = None
           return
        atexit.register(sys.exitfunc)
        atexit.register(self.__ircTopicThreadExitHandler)
     except Exception as e :
        print "Exception : {0}\r\n".format(e)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)

   def refreshTopic(self) :
       ircTopic=self.__irc_channel_topic()  

   def refreshMsg(self) :
       ircMsg=self.__irc_channel_msg_recv()

   def run(self) :
     global ircTopic
     global ircMsg
     try:    
        if self.__ircSocket == None :
           return
        self.isRunning=True
        while self.isRunning :
           self.refreshMsg()
           self.refreshTopic()
           #ircTopic=self.__irc_channel_topic()
           #time.sleep(self.__pauseAmt)
     except socket.error :
        isRunning=False
        self.__ircSocket.close()
        self.__ircSocket = None
     except Exception as e :
        print "Exception : {0}\r\n".format(e)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
     finally :
        isRunning=False
        self.__ircSocket.send(self.__quitCmd)
        self.__ircSocket.close()
          
   def __send_irc_cmd(self, cmd) :
      byteCt = len(cmd)
      sentCt = self.__ircSocket.send(cmd)
      if sentCt == byteCt:
         return True
      return False

   def __recv_irc_resp(self, respPattern, respHandler) :
     buf      = ""
     recvdResp=False
     while not recvdResp :
           try :
             buf=self.__ircSocket.recv(self.__rcvSize)
           except socket.timeout :
             pass
           if respPattern == None :
              return 
           if len(buf) > 0 :
              lines=buf.split(self.__eol)
              buf=""
              for line in lines:
                  if respPattern.search(line) != None :
                     result = None
                     if respHandler != None :
                        result = respHandler(line)
                     return result
           else :
               return 
     
   def __irc_channel_topic(self):
     global ircTopic
     try:    
        if self.__send_irc_cmd(self.__topicCmd) :
           topic = self.__recv_irc_resp(re.compile(settings.IRC_RSP_TOPIC),lambda l : l.split(self.__topicBoundary)[1])
        else :
           topic = self.__ircErrorMsg
     except Exception as e :
        print "Exception : {0}\r\n".format(e)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
     finally :
        if topic != None :
           ircTopic = topic
        return ircTopic

   def __irc_channel_msg_recv(self):
       global ircMsg
       try:
         msg = self.__recv_irc_resp(re.compile(settings.IRC_RSP_MSG),lambda l : l.split(self.__msgBoundary)[1])
       except Exception as e :
         print "Exception : {0}\r\n".format(e)
         exc_type, exc_value, exc_traceback = sys.exc_info()
         traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
       finally :
         if msg != None :
            ircMsg=msg

         return ircMsg

   def __ircTopicThreadExitHandler(self):
       print "TopicThread Exiting...."
