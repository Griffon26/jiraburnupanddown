#!/usr/bin/python

import copy
import datetime as dt
from dateutil import parser
import json
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pytz
import requests
import sys
import tzlocal

jiraVersion = 6

logging = False

config_file = '.jira-burn-up-and-down.rc'
config = {}

def saveConfiguration():
    with open(config_file, 'wt') as f:
        json.dump(config, f, indent = 2)

def loadConfiguration():
    global config
    try:
        with open(config_file, 'rt') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

def log(msg):
    print(msg)

def get_current_localtime():
    localzone = tzlocal.get_localzone()
    currentTime = dt.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(localzone)
    return currentTime

def timestamp_to_seconds(timestamp):
    epoch = dt.datetime.fromtimestamp(0, pytz.utc)
    return (timestamp - epoch).total_seconds()

def x_timestamps_to_seconds(x_y_data):
    return [[timestamp_to_seconds(x), y] for x, y in x_y_data]

def x_timestamps_to_seconds_np(x_y_data):
    return np.array([[timestamp_to_seconds(x), y] for x, y in x_y_data])

class JiraRest:

    def __init__(self, url, readFromFile = False, writeToFile = False):
        self.url = url
        self.read = readFromFile
        self.write = writeToFile
        self.auth = None

    def _get(self, resource, filename, params = None):
        if self.read:
            with open(filename, 'rt') as f:
                jsonData = json.load(f)
        else:
            r = requests.get('%s/%s' % (self.url, resource), params=params, auth=self.auth)
            r.raise_for_status()
            jsonData = r.json()

            if self.write:
                with open(filename, 'wt') as f:
                    json.dump(jsonData, f)

        return jsonData

class Jira6(JiraRest):

    def __init__(self, url, readFromFile = False, writeToFile = False):
        super().__init__(url, readFromFile = readFromFile, writeToFile = writeToFile)

    def setAuth(self, auth):
        self.auth = auth

    def getScrumBoards(self):
        jsonData = self._get('rest/greenhopper/1.0/xboard/selectorData', 'jira6/getScrumBoards.json')

        boards = {}
        for board in jsonData['rapidViews']:
            if board['sprintSupportEnabled']:
                boards[board['id']] = board['name']

        return boards

    def getSprints(self, boardId):
        jsonData = self._get('rest/greenhopper/1.0/sprintquery/%s' % boardId, 'jira6/getSprints.json', params = {
                'startAt' : 0,
                'maxResults' : 1000
            })

        sprints = {}
        for sprint in jsonData['sprints']:
            sprints[sprint['id']] = sprint

        return sprints

    def getSprintDates(self, boardId, sprints, sprintId):
        jsonData = self._get('rest/greenhopper/1.0/rapid/charts/sprintreport', 'jira6/getSprintDates.json', params = {
                'rapidViewId' : boardId,
                'sprintId' : sprintId
            })

        endDate = jsonData['sprint']['completeDate']
        if endDate == 'None':
            endDate = jsonData['sprint']['endDate']

        localzone = tzlocal.get_localzone()

        sprintStart = localzone.localize(parser.parse(jsonData['sprint']['startDate']))
        sprintEnd = localzone.localize(parser.parse(endDate))

        return sprintStart, sprintEnd

    def getKanbanBoards(self):
        jsonData = self._get('rest/greenhopper/1.0/xboard/selectorData', 'jira6/getKanbanBoards.json')

        boards = {}
        for view in jsonData['rapidViews']:
            if view['sprintSupportEnabled']:
                boards[view['id']] = view['name']

        return boards

    def getIssues(self, boardId, sprintId) :
        jsonData = self._get('rest/api/2/search', 'jira6/getIssues.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'issuetype = Sub-task and sprint = %s' % sprintId,
                'fields' : 'timetracking,resolutiondate'
            })

        return jsonData['issues']

    def getEffortForIssues(self, boardId, issueNames):
        jsonData = self._get('rest/api/2/search', 'jira6/getEffortForIssues.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'issuekey in (%s)' % ','.join(issueNames),
                'fields' : 'timetracking,resolutiondate'
            })

        effortForIssues = {}
        for issue in jsonData['issues']:
            if 'originalEstimateSeconds' in issue['fields']['timetracking']:
                effortForIssues[issue['key']] = issue['fields']['timetracking']['originalEstimateSeconds']
            else:
                effortForIssues[issue['key']] = 0

        return effortForIssues

    def getScopeChangeBurndownChart(self, rapidViewId, sprintId):
        jsonData = self._get('rest/greenhopper/1.0/rapid/charts/scopechangeburndownchart', 'jira6/getScopeChangeBurndownChart.json', params = {
                'rapidViewId' : rapidViewId,
                'sprintId' : sprintId
            })

        return jsonData

    def getIssueWorklogs(self, boardId, sprintStart, sprintEnd):
        jsonData = self._get('rest/api/2/search', 'jira6/getIssueWorklogs.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'jql' : '(resolved >= %s or resolution = unresolved) and ' % sprintStart + \
                        '(created <= %s) and (updated >= %s) and (issuetype = Support)' % (sprintEnd, sprintStart),
                'fields' : 'worklog'
            })

        return jsonData['issues']

class Jira7(JiraRest):

    def __init__(self, url, readFromFile = False, writeToFile = False):
        super().__init__(url, readFromFile = readFromFile, writeToFile = writeToFile)

    def setAuth(self, auth):
        self.auth = auth

    def getScrumBoards(self):
        jsonData = self._get('rest/agile/1.0/board', 'jira7/getScrumBoards.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'type' : 'scrum'
            })

        boards = {}
        for board in jsonData['values']:
            boards[board['id']] = board['name']

        return boards

    def getSprints(self, boardId):
        jsonData = self._get('rest/agile/1.0/board/%s/sprint' % boardId, 'jira7/getSprints.json', params = {
                'startAt' : 0,
                'maxResults' : 1000
            })

        sprints = {}
        for sprint in jsonData['values']:
            sprints[sprint['id']] = sprint

        return sprints

    def getSprintDates(self, boardId, sprints, sprintId):
        sprintStart = parser.parse(sprints[sprintId]['startDate'])
        sprintEnd = parser.parse(sprints[sprintId]['endDate'])

        return sprintStart, sprintEnd


    def getKanbanBoards(self):
        jsonData = self._get('rest/agile/1.0/board', 'jira7/getKanbanBoards.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'type' : 'kanban'
            })

        boards = {}
        for board in jsonData['values']:
            boards[board['id']] = board['name']

        return boards

    def getIssues(self, boardId, sprintId):
        jsonData = self._get('rest/agile/1.0/board/%s/sprint/%s/issue' % (boardId, sprintId), 'jira7/getIssues.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'issuetype = Sub-task',
                'fields' : 'timetracking,resolutiondate'
            })

        return jsonData['issues']

    def getEffortForIssues(self, boardId, issueNames):
        jsonData = self._get('rest/agile/1.0/board/%s/issue' % boardId, 'jira7/getEffortForIssues.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'issuekey in (%s)' % ','.join(issueNames),
                'fields' : 'timetracking'
            })

        effortForIssues = {}
        for issue in jsonData['issues']:
            if 'originalEstimateSeconds' in issue['fields']['timetracking']:
                effortForIssues[issue['key']] = issue['fields']['timetracking']['originalEstimateSeconds']
            else:
                effortForIssues[issue['key']] = 0

        return effortForIssues

    def getIssueWorklogs(self, boardId, sprintStart, sprintEnd):
        jsonData = self._get('rest/agile/1.0/board/%s/issue' % boardId, 'jira7/getIssueWorklogs.json', params = {
                'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'worklogDate >= %s and worklogDate <= %s and issuetype = Support' % (sprintStart, sprintEnd),
                'fields' : 'worklog'
            })

        return jsonDate['issues']

'''
  function popup(object)
  {
    alert(JSON.stringify(object, null, 8));
  }

'''
def byTimestamp(x):
    return timestamp_to_seconds(x[0])

def byResolutionDate(x):
    if x['fields']['resolutiondate']:
        result = timestamp_to_seconds(parser.parse(x['fields']['resolutiondate']))
    else:
        result = 0

    '''
    popup('(' + x.id + ',' + x.fields.resolutiondate + ') ' + ((result < 0) ? '<' :
                                                               (result > 0) ? '>' :
                                                                             '==') + ' (' + y.id + ',' + y.fields.resolutiondate + ')');
    '''
    return result

def createSegments(inputdata, connected):
    dataSet = [ inputdata[0] ]
    previousY = inputdata[0][1]

    for value in inputdata[1:]:
        dataSet.append([value[0], previousY])
        if not connected:
            dataSet.append(None)
        dataSet.append(value)
        previousY = value[1]

    return dataSet

def getZeroData(sprintStart, sprintEnd):
    return [[sprintStart, 0], [sprintEnd, 0]]

def createZeroLine(plotItem, zeroData):
    pen = pg.mkPen('k', width=1, style=QtCore.Qt.DashLine)
    pen.setDashPattern([10, 10])

    plotItem.plot(x_timestamps_to_seconds_np(zeroData), pen = pen)

def getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart):
    localzone = tzlocal.get_localzone()
    timezoneOffset = sprintStart - dt.datetime.fromtimestamp(int(scopeChangeBurndownChart['startTime']) / 1000, tz=pytz.utc)

    initialScope = []
    scopeChanges = []

    tmpSet = set()
    issueNames = []
    alreadyDone = set()

    for timestamp, changelist in scopeChangeBurndownChart['changes'].items():
        timestamp = dt.datetime.fromtimestamp(int(timestamp) / 1000, tz=localzone) + timezoneOffset

        for change in changelist:
            if ('column' in change and
                'done' in change['column'] and
                timestamp <= sprintStart):
                alreadyDone.add(change['key'])

    for timestamp, changelist in scopeChangeBurndownChart['changes'].items():
        timestamp = dt.datetime.fromtimestamp(int(timestamp) / 1000, tz=localzone) + timezoneOffset

        for change in changelist:
            # Skip parent issues
            if not scopeChangeBurndownChart['issueToParentKeys'][change['key']]:
                continue

            # Skip changes that are not sprint scope changes
            if 'added' not in change:
                continue

            # Ignore issues that were already completed before the sprint had started
            if change['key'] in alreadyDone:
                continue

            # Choose whether to add it to the initialScope or to the scopeChanges
            if timestamp <= sprintStart:
                initialScope.append( { 'timestamp' : timestamp,
                                       'added'     : change['added'],
                                       'issueName' : change['key'] } )
            elif timestamp <= sprintEnd:
                scopeChanges.append( { 'timestamp' : timestamp,
                                       'added'     : change['added'],
                                       'issueName' : change['key'] } )

            if change['key'] not in tmpSet:
                tmpSet.add(change['key'])
                issueNames.append(change['key']);

    initialScope.sort(key = lambda x: timestamp_to_seconds(x['timestamp']))
    scopeChanges.sort(key = lambda x: timestamp_to_seconds(x['timestamp']))

    return { 'names' : issueNames,
             'initial' : initialScope,
             'changes' : scopeChanges }

def getInitialScope(initialIssues, effortForIssues):
    initialScope = 0

    log('Calculating initial sprint scope')

    for issue in initialIssues:
        effort = effortForIssues[issue['issueName']] / 3600
        initialScope += effort;
        log("  adding %s: %.2f hours" % (issue['issueName'], effort))

    log("  Initial sprint scope is %.2f hours" % initialScope)

    return initialScope

def calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues, effortForIssues):
    scope = 0
    scopeChanges = []

    log('Calculating sprint scope changes')

    scopeChanges.append( [ copy.deepcopy(sprintStart), 0 ] );

    for scopeChange in scopeChangingIssues:
        effort = effortForIssues[scopeChange['issueName']] / 3600

        if scopeChange['added']:
            scope += effort
            log('  added %s: %.2f hours at %s' % (scopeChange['issueName'], effort, scopeChange['timestamp']))
        else:
            scope -= effort
            log('  removed %s: %.2f hours at %s' % (scopeChange['issueName'], effort, scopeChange['timestamp']))

        scopeChanges.append( [ copy.deepcopy(scopeChange['timestamp']), scope ] )

    log('  Overall scope change: %.2f hours' % scope)

    scopeChanges.append( [ copy.deepcopy(sprintEnd), scope ] )

    return scopeChanges

def createSprintScopeLine(plotItem, data):
    endScope = data[-1][1];
    lineData = [[value[0], endScope - value[1]] for value in data]

    pen = pg.mkPen('k', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(createSegments(lineData, True)), pen = pen)

def getIdealBurndown(sprintStart, sprintEnd, finalSprintScope):
    return [ [copy.deepcopy(sprintStart), finalSprintScope], [copy.deepcopy(sprintEnd), 0] ]

def createIdealBurndownLine(plotItem, idealBurndownData):
    pen = pg.mkPen('#c0c0c0', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(idealBurndownData), pen = pen)

def getActualBurndown(sprintStart, sprintEnd, finalSprintScope, issues):
    totalEffortCompleted = 0
    remainingSprintEffort = finalSprintScope
    actual = [ [sprintStart, remainingSprintEffort] ]

    log('Calculating actual burndown')

    for value in issues:
        if not value['fields']['resolutiondate']:
            continue
        else:
            resolutionDate = parser.parse(value['fields']['resolutiondate'])
            if resolutionDate >= sprintStart and \
               resolutionDate <= sprintEnd:
                if value['fields']['timetracking']['originalEstimateSeconds']:
                    completedEffort = value['fields']['timetracking']['originalEstimateSeconds'] / 3600
                    totalEffortCompleted += completedEffort
                    remainingSprintEffort -= completedEffort
                    actual.append([resolutionDate, remainingSprintEffort])
                    log('  completed %s: %.2f hours at %s' % (value['key'], completedEffort, resolutionDate))

    log('  Overall effort completed: %.2f hours' % totalEffortCompleted)

    currentDate = get_current_localtime()

    lastDate = currentDate if currentDate < sprintEnd else sprintEnd

    actual.append([copy.deepcopy(lastDate), remainingSprintEffort])

    return actual

def createActualBurndownLine(plotItem, actualBurndownData):
    pen = pg.mkPen('b', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(createSegments(actualBurndownData, True)), pen = pen)

def adjustForHiddenWeekends(points, weekends):
    upcomingWeekends = weekends[:]
    pointIndex = 0;

    accumulatedOffset = dt.timedelta(0)

    while pointIndex < len(points):
        nextPoint = points[pointIndex]

        '''
        popup({ 'nextPoint' : nextPoint,
                  'nextWeekend' : nextWeekend,
                  'points' : points,
                  'weekends' : weekends,
                  'accum' : accumulatedOffset.humanize() });
        '''
        if upcomingWeekends:
            nextWeekend = upcomingWeekends[0]
        else:
            nextWeekend = None

        if nextWeekend and nextPoint[0] > nextWeekend['start']:
            if nextPoint[0] > nextWeekend['start'] + nextWeekend['duration']:
                accumulatedOffset += nextWeekend['duration']
                upcomingWeekends.pop(0)
            else:
                nextPoint[0] = nextWeekend['start'] - accumulatedOffset
                pointIndex += 1
        else:
            nextPoint[0] -= accumulatedOffset
            pointIndex += 1
    '''
    popup({ 'points' : points,
            'weekends' : weekends,
            'accum' : accumulatedOffset.humanize() });
            '''
    return points

def determineSprintWeekends(sprintStart, sprintEnd):
    endOfWeek = sprintStart.replace(hour = 0, minute = 0, second = 0, microsecond = 0) + \
                dt.timedelta(days = 7 - sprintStart.weekday())
    startOfWeekend = endOfWeek - dt.timedelta(days = 2)
    weekends = []

    while startOfWeekend < sprintEnd:
        startOfNonWork = max(sprintStart, startOfWeekend)
        endOfNonWork = min(sprintEnd, endOfWeek)

        weekends.append( { 'start' : startOfNonWork,
                           'duration' : endOfNonWork - startOfNonWork } )

        endOfWeek += dt.timedelta(weeks = 1)
        startOfWeekend = endOfWeek - dt.timedelta(days = 2)
    return weekends

def createDayLabels(sprintStart, sprintEnd):
    labels = []
    day = sprintStart.replace(hour=12, minute=0, second = 0, microsecond = 0)
    if day < sprintStart:
        day += dt.timedelta(days = 1)

    while day < sprintEnd:
        if day.weekday() not in [5, 6]:
            labels.append([copy.deepcopy(day), day.strftime('%a')])

        day += dt.timedelta(days = 1)

    return labels

def createDayLines(sprintStart, sprintEnd):
    lines = []
    day = sprintStart.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    if day < sprintStart:
        day += dt.timedelta(days = 1)

    while day < sprintEnd:
        if day.weekday() not in [5, 6]:
            lines.append([copy.deepcopy(day), None])

        day += dt.timedelta(days = 1)

    return lines

def createGridLineMarkings(plotItem, gridData):
    targetRect = plotItem.getViewBox().targetRect()
    min_y = targetRect.top()
    max_y = targetRect.bottom()

    markings = [ [ (value[0], min_y), (value[0], max_y) ] for value in gridData ]

    pen = pg.mkPen('#e0e0e0', width=1)
    for marking in markings:
        plotItem.plot(x_timestamps_to_seconds_np(marking), pen = pen)

def calculateActualBurnup(sprintStart, sprintEnd, issueWorklogs, burnupBudget, pointsPerHour):
    totalHoursIn = 0
    totalHoursOut = 0
    timeSpent = []

    log('Calculating support burnup')

    for issue in issueWorklogs:
        for worklog in issue['fields']['worklog']['worklogs']:
            created = parser.parse(worklog['created'])
            if created >= sprintStart and created <= sprintEnd:
                timeSpent.append([created, worklog['timeSpentSeconds']])
                totalHoursIn += worklog['timeSpentSeconds'] / 3600
                log('  adding %s: %.2f hours' % (issue['key'], worklog['timeSpentSeconds'] / 3600))
            else:
                totalHoursOut += worklog['timeSpentSeconds'] / 3600;
                log('  skipping %s: %.2f hours' % (issue['key'], worklog['timeSpentSeconds'] / 3600))

    log('  Added a total of %.2f hours from worklogs' % totalHoursIn)
    log('  Skipped a total of %.2f hours from worklogs' % totalHoursOut)

    timeSpent.sort(key=byTimestamp)

    totalTimeSpent = 0
    burnup = [ [sprintStart, -burnupBudget * pointsPerHour] ]
    for ts in timeSpent:
        totalTimeSpent += ts[1]
        burnup.append([ts[0], ((totalTimeSpent / 3600) - burnupBudget) * pointsPerHour])
    currentDate = get_current_localtime()
    lastDate = currentDate if currentDate < sprintEnd else sprintEnd
    burnup.append([copy.deepcopy(lastDate), ((totalTimeSpent / 3600) - burnupBudget) * pointsPerHour]);

    return burnup

def createActualBurnupLine(plotItem, actualBurnupData):
    pen = pg.mkPen('r', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(createSegments(actualBurnupData, True)), pen = pen)

# This function is a bit different because it calculates data from a line
# from which the weekends have already been removed. This makes it easier to
# calculate the slope of the projected burnup.
def calculateProjectedBurnup(zeroData, actualBurnupData):
    burnupStart = actualBurnupData[0][0];
    burnupStartHeight = actualBurnupData[0][1];
    burnupEnd = actualBurnupData[-1][0];
    burnupEndHeight = actualBurnupData[-1][1];

    sprintStart = zeroData[0][0];
    sprintEnd = zeroData[-1][0];

    projectedBurnupHeight = ((burnupEndHeight - burnupStartHeight) / (burnupEnd - burnupStart).total_seconds()) * (sprintEnd - sprintStart).total_seconds() + burnupStartHeight;

    return [ [copy.deepcopy(burnupEnd), burnupEndHeight], [copy.deepcopy(sprintEnd), projectedBurnupHeight] ]

def createProjectedBurnupLine(plotItem, projectedBurnupData):
    pen = pg.mkPen('r', width=1, style=QtCore.Qt.DashLine)
    pen.setDashPattern([10, 10])
    plotItem.plot(x_timestamps_to_seconds_np(projectedBurnupData), pen = pen)

def calculateIdealBurnup(sprintStart, sprintEnd, burnupBudget):
    return [ [copy.deepcopy(sprintStart), -burnupBudget], [copy.deepcopy(sprintEnd), 0] ]

def createIdealBurnupLine(plotItem, idealBurnupData):
    pen = pg.mkPen('#c0c0c0', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(idealBurnupData), pen = pen)

def calculateExpectedBurndown(sprintStart, sprintEnd, finalSprintScope, projectedBurnupHeight):
    if projectedBurnupHeight < 0:
        return [ [copy.deepcopy(sprintStart), finalSprintScope], [copy.deepcopy(sprintEnd), projectedBurnupHeight] ]
    else:
        return []

def createExpectedBurndownLine(plotItem, expectedBurndownData):
    pen = pg.mkPen('#008000', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(expectedBurndownData), pen = pen)

def annotateBudgetOverrun(plotItem, max_x, projectedBurnupHeight):
    '''
  {
    var placeholder = $("#placeholder");

    var topEnd = plot.pointOffset({ x: max_x, y: projectedBurnupHeight });
    var bottomEnd = plot.pointOffset({ x: max_x, y: 0 });

    var spaceForText = bottomEnd.top - topEnd.top;

    if(spaceForText >= 30)
    {
      // Draw a little arrow on top of the last label to demonstrate canvas
      // drawing

      var arrowWidth = 2;
      var arrowHeight = 10;

      var ctx = plot.getCanvas().getContext("2d");
      topEnd.left += 2;
      ctx.beginPath();
      ctx.lineWidth = 1;
      ctx.moveTo(topEnd.left - arrowWidth, topEnd.top + arrowHeight);
      ctx.lineTo(topEnd.left, topEnd.top);
      ctx.lineTo(topEnd.left + arrowWidth, topEnd.top + arrowHeight);
      ctx.moveTo(topEnd.left, topEnd.top);
      ctx.lineTo(topEnd.left, bottomEnd.top);
      ctx.lineTo(topEnd.left - arrowWidth, bottomEnd.top - arrowHeight);
      ctx.moveTo(topEnd.left, bottomEnd.top);
      ctx.lineTo(topEnd.left + arrowWidth, bottomEnd.top - arrowHeight);
      ctx.stroke();

      placeholder.append("<div style='position:absolute;left:" + (topEnd.left + 4) + "px;top:" + topEnd.top + "px;color:#666;font-size:smaller'>" +
                         "<p style='vertical-align:middle;display:table-cell;height:" + spaceForText + "px;'>" + Math.round(projectedBurnupHeight) + " points</p></div>");
    }
  }
    '''
    pass

def updateChart(jira, plotItem, sprints, boardId, supportBoardId, sprintId, burnupBudget, availability):
    #
    # Gather all data
    #
    sprintStart, sprintEnd = jira.getSprintDates(boardId, sprints, sprintId)

    log("Sprint start is %s" % sprintStart)
    log("Sprint end   is %s" % sprintEnd)

    weekends = determineSprintWeekends(sprintStart, sprintEnd)

    zeroData = getZeroData(sprintStart, sprintEnd)
    axisData = createDayLabels(sprintStart, sprintEnd)
    gridData = createDayLines(sprintStart, sprintEnd)


    # Burndown
    scopeChangeBurndownChart = jira.getScopeChangeBurndownChart(boardId, sprintId)
    scopeChangingIssues = getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart)
    effortForIssues = jira.getEffortForIssues(boardId, scopeChangingIssues['names'])

    initialSprintScope = getInitialScope(scopeChangingIssues['initial'], effortForIssues)
    sprintScopeData = calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues['changes'], effortForIssues)

    finalSprintScope = initialSprintScope + sprintScopeData[-1][1]

    idealBurndownData = getIdealBurndown(sprintStart, sprintEnd, finalSprintScope)

    issues = jira.getIssues(boardId, sprintId)
    issues.sort(key=byResolutionDate)
    actualBurndownData = getActualBurndown(sprintStart, sprintEnd, finalSprintScope, issues)


    # Burnup

    pointsPerHour = initialSprintScope / (availability - burnupBudget)

    issueWorklogs = jira.getIssueWorklogs(supportBoardId, sprintStart, sprintEnd)
    actualBurnupData = calculateActualBurnup(sprintStart, sprintEnd, issueWorklogs, burnupBudget, pointsPerHour)

    idealBurnupData = calculateIdealBurnup(sprintStart, sprintEnd, burnupBudget * pointsPerHour)



    # 
    # Remove all weekends
    #
    adjustForHiddenWeekends(zeroData, weekends)
    adjustForHiddenWeekends(sprintScopeData, weekends)
    adjustForHiddenWeekends(idealBurndownData, weekends)
    adjustForHiddenWeekends(actualBurndownData, weekends)
    adjustForHiddenWeekends(axisData, weekends)
    adjustForHiddenWeekends(gridData, weekends)
    adjustForHiddenWeekends(actualBurnupData, weekends)
    adjustForHiddenWeekends(idealBurnupData, weekends)

    projectedBurnupData = calculateProjectedBurnup(zeroData, actualBurnupData)

    projectedBurnupHeight = projectedBurnupData[-1][1]
    expectedBurndownData = calculateExpectedBurndown(sprintStart, sprintEnd, finalSprintScope, projectedBurnupHeight)
    adjustForHiddenWeekends(expectedBurndownData, weekends)


    # 
    # Plot
    #

    plotItem.getAxis('bottom').setTicks([x_timestamps_to_seconds(axisData)])
    plotItem.setXRange(timestamp_to_seconds(zeroData[0][0]),
                       timestamp_to_seconds(zeroData[-1][0]),
                       padding = 0)
    plotItem.setYRange(-burnupBudget * pointsPerHour, finalSprintScope, padding = 0)

    createGridLineMarkings(plotItem, gridData)
    createIdealBurndownLine(plotItem, idealBurndownData)
    createIdealBurnupLine(plotItem, idealBurnupData)
    createZeroLine(plotItem, zeroData)
    createSprintScopeLine(plotItem, sprintScopeData)
    createActualBurndownLine(plotItem, actualBurndownData)
    createActualBurnupLine(plotItem, actualBurnupData)
    createProjectedBurnupLine(plotItem, projectedBurnupData)
    createExpectedBurndownLine(plotItem, expectedBurndownData)

    annotateBudgetOverrun(plotItem, zeroData[-1][0], projectedBurnupHeight)

def initializePlot(plotItem):
    #plotItem.showGrid(True, True, 0.3)
    plotItem.hideButtons()
    plotItem.setMenuEnabled(enableMenu = False)
    plotItem.getViewBox().setMouseEnabled(x = False, y = False)

    plotItem.showGrid(x = False, y = True, alpha = 0.3)
    plotItem.getAxis('bottom').setStyle(tickLength = 0)
    plotItem.getAxis('left').setStyle(tickLength = 0)

if __name__ == '__main__':
    app = QtGui.QApplication([])

    loadConfiguration()

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('antialias', True)

    mw = QtGui.QMainWindow()
    cw = QtGui.QWidget()
    mw.setCentralWidget(cw)
    l = QtGui.QVBoxLayout()
    cw.setLayout(l)

    pw = pg.PlotWidget(name='Plot1')
    l.addWidget(pw)


    pi = pw.getPlotItem()

    mw.show()

    initializePlot(pi)


    # There are two ways to use this script without a real Jira server.
    # The first is to have this script read its data from files by setting
    # readFromFile = True when creating an instance of the Jira class.
    # The second is to start up the fakejira.py script and have this script
    # connect to localhost:8080.

    jiraClass = Jira6 if jiraVersion == 6 else Jira7
    jira = jiraClass(config['jiraurl'], readFromFile = False, writeToFile = False)

    boards = jira.getScrumBoards()
    print('All available board IDs are: %s' % boards)
    boardId = 8
    sprints = jira.getSprints(boardId)
    sprintId = 533
    print('All available sprints for board %s are: %s' % (boardId, sprints))
    updateChart(jira, pi, sprints, boardId, None, sprintId, 100, 500)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

    saveConfiguration()


