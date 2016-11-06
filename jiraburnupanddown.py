#!/usr/bin/python

# Copyright 2016 Maurice van der Pot <griffon26@kfk4ever.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

def key_strings_to_int(d):
    return dict( (int(k),(key_strings_to_int(v) if isinstance(v, dict) else v)) for k,v in d.items())

def loadConfiguration():
    global config
    try:
        with open(config_file, 'rt') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    if 'hours' not in config:
        config['hours'] = {}
    config['hours'] = key_strings_to_int(config['hours'])

    if 'jiraurl' not in config:
        config['jiraurl'] = 'http://127.0.0.1:8080'
        
    if 'username' not in config:
        config['username'] = ''

    if 'currentBoard' not in config:
        config['currentBoard'] = None

    if 'currentSprint' not in config:
        config['currentSprint'] = None

def log(msg):
    print(msg)

def timestamp_to_seconds(timestamp):
    epoch = dt.datetime.fromtimestamp(0, pytz.utc)
    return (timestamp - epoch).total_seconds()

def x_timestamps_to_seconds(x_y_data):
    return [[timestamp_to_seconds(x), y] for x, y in x_y_data]

def x_timestamps_to_seconds_np(x_y_data):
    return np.array([[timestamp_to_seconds(x), y] for x, y in x_y_data])
    
def timestamp_to_jqltimestamp(ts):
    localzone = tzlocal.get_localzone()
    if str(ts.tzinfo) != str(localzone):
        raise RuntimeError('Timezone of timestamp (%s) is not equal to local timezone (%s)' % (repr(ts.tzinfo), repr(localzone)))
    return ts.strftime('"%Y-%m-%d %H:%M"')

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
            print('--------------------------------\n%s/%s %s' % (self.url, resource, params))
            r = requests.get('%s/%s' % (self.url, resource), params=params, auth=self.auth, verify=False)
            r.raise_for_status()
            jsonData = r.json()

            if self.write:
                with open(filename, 'wt') as f:
                    json.dump(jsonData, f)

        return jsonData
        
    def setConnectionData(self, url, username, password):
        self.url = url
        self.auth = (username, password)

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

    def getSprintDates(self, boardId, sprintId):
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
        effortForIssues = {}
        if issueNames:
            jsonData = self._get('rest/api/2/search', 'jira6/getEffortForIssues.json', params = {
                    'startAt' : 0,
                    'maxResults' : 1000,
                    'jql' : 'issuekey in (%s)' % ','.join(issueNames),
                    'fields' : 'timetracking,resolutiondate'
                })

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
                'jql' : '(resolved >= %s or resolution = unresolved) and ' % timestamp_to_jqltimestamp(sprintStart) + \
                        '(created <= %s) and (updated >= %s) and (issuetype = Support)' % (timestamp_to_jqltimestamp(sprintEnd), timestamp_to_jqltimestamp(sprintStart)),
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

    def getSprintDates(self, boardId, sprintId):
        # TODO: get sprint information from jira
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

def byTimestamp(x):
    return timestamp_to_seconds(x[0])

def byResolutionDate(x):
    if x['fields']['resolutiondate']:
        result = timestamp_to_seconds(parser.parse(x['fields']['resolutiondate']))
    else:
        result = 0

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

def parseBurndownTimestamp(ts):
    localzone = tzlocal.get_localzone()
    naive = dt.datetime.fromtimestamp(int(ts) / 1000, tz = pytz.utc).replace(tzinfo = None)
    return localzone.localize(naive)

def getCurrentTimeFromBurndown(scopeChangeBurndownChart):
    return parseBurndownTimestamp(scopeChangeBurndownChart['now'])

def getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart):
    initialScope = []
    scopeChanges = []

    tmpSet = set()
    issueNames = []
    alreadyDone = set()

    for timestamp, changelist in scopeChangeBurndownChart['changes'].items():
        timestamp = parseBurndownTimestamp(timestamp)

        for change in changelist:
            if ('column' in change and
                'done' in change['column'] and
                timestamp <= sprintStart):
                alreadyDone.add(change['key'])

    for timestamp, changelist in scopeChangeBurndownChart['changes'].items():
        timestamp = parseBurndownTimestamp(timestamp)

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

def getIdealBurndownValueAtTimestamp(ts, idealBurndownData):
    startTimestamp = idealBurndownData[0][0]
    endTimestamp = idealBurndownData[-1][0]
    finalSprintScope = idealBurndownData[0][1]
    return (endTimestamp - ts) / (endTimestamp - startTimestamp) * finalSprintScope

def createIdealBurndownLine(plotItem, idealBurndownData):
    pen = pg.mkPen('#c0c0c0', width=2)
    plotItem.plot(x_timestamps_to_seconds_np(idealBurndownData), pen = pen)

def getActualBurndown(sprintStart, sprintEnd, currentTime, finalSprintScope, issues):
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

    lastDate = currentTime if currentTime < sprintEnd else sprintEnd

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

def calculateActualBurnup(sprintStart, sprintEnd, currentTime, issueWorklogs, burnupBudget, pointsPerHour):
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

    lastDate = currentTime if currentTime < sprintEnd else sprintEnd
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


def drawVerticalAnnotatedArrow(plotItem, x, y1, y2, text, xanchor):
    pen = pg.mkPen('k', width=1)

    arrowTop = max(y1, y2)
    arrowBottom = min(y1, y2)

    arrowLine = [ (x, arrowTop),
                  (x, arrowBottom) ]
    plotItem.plot(np.array(arrowLine), pen = pen)

    plotItem.addItem(pg.ArrowItem(pos = (x, arrowTop), angle = 90, tipAngle = 40, headLen=10, pen = None, brush = 'k'))
    plotItem.addItem(pg.ArrowItem(pos = (x, arrowBottom), angle = -90, tipAngle = 40, headLen=10, pen = None, brush = 'k'))

    textItem = pg.TextItem(text=text, color='k', anchor=(xanchor, 0.5))
    textItem.setPos(x, (arrowTop + arrowBottom) / 2)
    plotItem.addItem(textItem)

def annotateBudgetOverrun(plotItem, max_x, projectedBurnupHeight):
    max_x = timestamp_to_seconds(max_x)

    points = round(abs(projectedBurnupHeight))
    if points >= 2:
        drawVerticalAnnotatedArrow(plotItem, max_x, 0, projectedBurnupHeight, '%d pts' % points, 0)

def annotatePointsBehind(plotItem, currentTimestamp, currentIdealBurndownValue, currentActualBurndownValue):
    x = timestamp_to_seconds(currentTimestamp)

    points = round(abs(currentIdealBurndownValue - currentActualBurndownValue))
    if points >= 2:
        drawVerticalAnnotatedArrow(plotItem, x, currentIdealBurndownValue, currentActualBurndownValue, '%d pts' % points, 1)

def updateChart(jira, plotItem, boardId, supportBoardId, sprintId, burnupBudget, availability):
    #
    # Gather all data
    #
    sprintStart, sprintEnd = jira.getSprintDates(boardId, sprintId)

    log("Sprint start is %s" % sprintStart)
    log("Sprint end   is %s" % sprintEnd)

    weekends = determineSprintWeekends(sprintStart, sprintEnd)

    zeroData = getZeroData(sprintStart, sprintEnd)
    axisData = createDayLabels(sprintStart, sprintEnd)
    gridData = createDayLines(sprintStart, sprintEnd)


    # Burndown
    scopeChangeBurndownChart = jira.getScopeChangeBurndownChart(boardId, sprintId)
    scopeChangingIssues = getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart)
    currentTime = getCurrentTimeFromBurndown(scopeChangeBurndownChart)
    effortForIssues = jira.getEffortForIssues(boardId, scopeChangingIssues['names'])

    initialSprintScope = getInitialScope(scopeChangingIssues['initial'], effortForIssues)
    sprintScopeData = calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues['changes'], effortForIssues)

    finalSprintScope = initialSprintScope + sprintScopeData[-1][1]

    idealBurndownData = getIdealBurndown(sprintStart, sprintEnd, finalSprintScope)

    issues = jira.getIssues(boardId, sprintId)
    issues.sort(key=byResolutionDate)
    actualBurndownData = getActualBurndown(sprintStart, sprintEnd, currentTime, finalSprintScope, issues)


    # Burnup

    try:
        pointsPerHour = initialSprintScope / (availability - burnupBudget)
    except ZeroDivisionError:
        pointsPerHour = 0

    issueWorklogs = jira.getIssueWorklogs(supportBoardId, sprintStart, sprintEnd)
    actualBurnupData = calculateActualBurnup(sprintStart, sprintEnd, currentTime, issueWorklogs, burnupBudget, pointsPerHour)

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

    plotItem.clear()
    plotItem.getAxis('bottom').setTicks([x_timestamps_to_seconds(axisData)])

    min_x = timestamp_to_seconds(zeroData[0][0])
    max_x = timestamp_to_seconds(zeroData[-1][0]) + 24 * 3600
    min_y = -burnupBudget * pointsPerHour * 1.1
    max_y = finalSprintScope * 1.05

    plotItem.setRange(QtCore.QRectF(min_x, min_y, max_x - min_x, max_y - min_y), padding = 0)

    createGridLineMarkings(plotItem, gridData)
    createIdealBurndownLine(plotItem, idealBurndownData)
    createIdealBurnupLine(plotItem, idealBurnupData)
    createZeroLine(plotItem, zeroData)
    createSprintScopeLine(plotItem, sprintScopeData)
    createActualBurndownLine(plotItem, actualBurndownData)
    createActualBurnupLine(plotItem, actualBurnupData)
    createProjectedBurnupLine(plotItem, projectedBurnupData)
    createExpectedBurndownLine(plotItem, expectedBurndownData)

    currentTimestamp, currentActualBurndownValue = actualBurndownData[-1]
    currentIdealBurndownValue = getIdealBurndownValueAtTimestamp(currentTimestamp, idealBurndownData)

    annotateBudgetOverrun(plotItem, zeroData[-1][0], projectedBurnupHeight)
    annotatePointsBehind(plotItem, currentTimestamp, currentIdealBurndownValue, currentActualBurndownValue)

class ConnectionDialog(QtGui.QDialog):

    def __init__(self, jiraUrl, username, password):
        super().__init__()
        
        self.jiraUrlLabel = QtGui.QLabel('JIRA URL')
        self.jiraUrlEdit = QtGui.QLineEdit(jiraUrl)
        self.usernameLabel = QtGui.QLabel('User')
        self.usernameEdit = QtGui.QLineEdit(username)
        self.passwordLabel = QtGui.QLabel('Password')
        self.passwordEdit = QtGui.QLineEdit(password)
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setText('Connect')
        
        self.gridLayout = QtGui.QGridLayout(self)
        self.gridLayout.addWidget(self.jiraUrlLabel, 0, 0)
        self.gridLayout.addWidget(self.jiraUrlEdit, 0, 1)
        self.gridLayout.addWidget(self.usernameLabel, 1, 0)
        self.gridLayout.addWidget(self.usernameEdit, 1, 1)
        self.gridLayout.addWidget(self.passwordLabel, 2, 0)
        self.gridLayout.addWidget(self.passwordEdit, 2, 1)
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
    def getConnectionData(self):
        return (self.jiraUrlEdit.text(), self.usernameEdit.text(), self.passwordEdit.text())
    
class Gui(QtCore.QObject):
    ''' The Gui class is responsible for constructing all widgets and emitting
        signals when the user changes any of the inputs. It provides methods
        for updating the list of boards or sprints that can be selected, as
        well as functions for setting the current board, sprint, availability
        and burnupBudget, but does not perform checks on the relations between
        them as that is left to the model.
    '''

    boardChanged = QtCore.pyqtSignal(int)
    sprintChanged = QtCore.pyqtSignal(int)
    availabilityChanged = QtCore.pyqtSignal(int)
    burnupBudgetChanged = QtCore.pyqtSignal(int)
    connectionDataChanged = QtCore.pyqtSignal(str, str, str)

    def __init__(self, jiraUrl, username, password):
        super().__init__()
        
        self.jiraUrl = jiraUrl
        self.username = username
        self.password = password

        self.main_window = QtGui.QMainWindow()
        self.main_window.setWindowTitle('JIRA burn-up-and-down')
        
        central_widget = QtGui.QWidget()
        self.main_window.setCentralWidget(central_widget)
		
        configConnectionButton = QtGui.QPushButton('Configure connection...')
        configConnectionButton.clicked.connect(self.openConnectionDialog)
        
        connectionStatusLabel = QtGui.QLabel('Connection status')
        self.connectionStatusText = QtGui.QLabel('')
        self.connectionStatusText.setWordWrap(True)

        boardLabel = QtGui.QLabel('Scrum board')
        sprintLabel = QtGui.QLabel('Sprint')
        availabilityLabel = QtGui.QLabel('Availability (hours)')
        burnupBudgetLabel = QtGui.QLabel('Burnup budget (hours)')

        self.boards_combobox = QtGui.QComboBox()
        self.boards_combobox.activated.connect(self._boardSelectionChanged)
        self.boards_combobox.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.sprints_combobox = QtGui.QComboBox()
        self.sprints_combobox.activated.connect(self._sprintSelectionChanged)
        self.sprints_combobox.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.plot_widget = pg.PlotWidget(name='Plot1')

        self.availabilityEdit = QtGui.QLineEdit()
        self.availabilityEdit.setValidator(QtGui.QIntValidator())
        self.availabilityEdit.editingFinished.connect(self._availabilityChanged)
        self.burnupBudgetEdit = QtGui.QLineEdit()
        self.burnupBudgetEdit.setValidator(QtGui.QIntValidator())
        self.burnupBudgetEdit.editingFinished.connect(self._burnupBudgetChanged)

        gridLayout = QtGui.QGridLayout()
        central_widget.setLayout(gridLayout)

        gridLayout.addWidget(configConnectionButton, 0, 0, 1, 2)
        gridLayout.addWidget(connectionStatusLabel, 0, 2)
        gridLayout.addWidget(self.connectionStatusText, 0, 3, 1, 1)
        
        gridLayout.addWidget(boardLabel, 1, 0)
        gridLayout.addWidget(self.boards_combobox, 1, 1)
        gridLayout.addWidget(sprintLabel, 2, 0) 
        gridLayout.addWidget(self.sprints_combobox, 2, 1)
        gridLayout.addWidget(availabilityLabel, 1, 2)
        gridLayout.addWidget(self.availabilityEdit, 1, 3)
        gridLayout.addWidget(burnupBudgetLabel, 2, 2)
        gridLayout.addWidget(self.burnupBudgetEdit, 2, 3)
        gridLayout.addWidget(self.plot_widget, 3, 0, 1, 4)

        self.main_window.show()

    def getPlotWidget(self):
        return self.plot_widget

    def setConnectionStatus(self, text):
        self.connectionStatusText.setText(text)
    
    def setAvailability(self, availability):
        self.availabilityEdit.setText(availability)

    def setBurnupBudget(self, burnupBudget):
        self.burnupBudgetEdit.setText(burnupBudget)
        
    def updateAvailableBoards(self, boards):
        self.boards_combobox.clear()
        for boardName, boardId in sorted((boardName, boardId) for boardId, boardName in boards):
            self.boards_combobox.addItem(boardName, boardId)

    def updateAvailableSprints(self, sprints):
        self.sprints_combobox.clear()
        for sprintId, sprintName in sorted(sprints):
            self.sprints_combobox.addItem(sprintName, sprintId)

    def updateHours(self, boardId, sprintId, availability, burnupBudget):
        index = self.boards_combobox.findData(boardId)
        self.boards_combobox.setCurrentIndex(index)

        index = self.sprints_combobox.findData(sprintId)
        self.sprints_combobox.setCurrentIndex(index)

        self.availabilityEdit.setText(str(availability))
        self.burnupBudgetEdit.setText(str(burnupBudget))

    def _boardSelectionChanged(self, boardIndex):
        boardId = self.boards_combobox.itemData(boardIndex)
        self.boardChanged.emit(boardId)

    def _sprintSelectionChanged(self, sprintIndex):
        sprintId = self.sprints_combobox.itemData(sprintIndex)
        self.sprintChanged.emit(sprintId)

    def _availabilityChanged(self):
        self.availabilityChanged.emit(int(self.availabilityEdit.text()))

    def _burnupBudgetChanged(self):
        self.burnupBudgetChanged.emit(int(self.burnupBudgetEdit.text()))
        
    def openConnectionDialog(self):
        connectionDialog = ConnectionDialog(self.jiraUrl, self.username, self.password)
        if connectionDialog.exec_() == QtGui.QDialog.Accepted:
            self.jiraUrl, self.username, self.password = connectionDialog.getConnectionData()
            self.connectionDataChanged.emit(self.jiraUrl, self.username, self.password)
            
class Chart():
    ''' Chart draws a burndown chart on a plotItem given a boardId, sprintId,
        availability and burnupBudget. It requests all other data about the
        given sprint from Jira.
    '''
    def __init__(self, jira, plotItem):
        self.jira = jira
        self.plotItem = plotItem

        self.boardId = None
        self.sprintId = None
        self.burnupBudget = 0
        self.availability = 0

        self.plotItem.hideButtons()
        self.plotItem.setMenuEnabled(enableMenu = False)
        self.plotItem.getViewBox().setMouseEnabled(x = False, y = False)

        self.plotItem.showGrid(x = False, y = True, alpha = 0.3)
        self.plotItem.getAxis('bottom').setStyle(tickLength = 0)
        self.plotItem.getAxis('left').setStyle(tickLength = 0)

    def updateChart(self, boardId, sprintId, availability, burnupBudget):
        self.boardId = boardId
        self.sprintId = sprintId
        self.availability = availability
        self.burnupBudget = burnupBudget
        self._updateChartIfPossible()

    def setSupportBoard(self, supportBoardId):
        pass

    def _updateChartIfPossible(self):
        if (self.boardId != None and
            self.sprintId != None):
            updateChart(self.jira, self.plotItem, self.boardId, None, self.sprintId, self.burnupBudget, self.availability)

class HoursManager():
    ''' HoursManager maintains the availability and burnupBudget associated
        with each sprint.
    '''
    def __init__(self, hours):
        self.hours = copy.deepcopy(hours)

    def getHours(self, boardId, sprintId):
        if boardId not in self.hours:
            self.hours[boardId] = {}

        if sprintId not in self.hours[boardId]:
            self.hours[boardId][sprintId] = (0, 0)

        return self.hours[boardId][sprintId]

    def setAvailability(self, boardId, sprintId, availability):
        _, old_budget = self.getHours(boardId, sprintId)
        self.hours[boardId][sprintId] = (availability, old_budget)

    def setBurnupBudget(self, boardId, sprintId, burnupBudget):
        old_avail, _ = self.getHours(boardId, sprintId)
        self.hours[boardId][sprintId] = (old_avail, burnupBudget)

class Model(QtCore.QObject):
    ''' Model maintains the available boards and sprints as well as the
        currently selected board, sprint, availability and burnupBudget.
        It makes sure they are always consistent, for instance when a different
        board is selected and the currently selected sprint is no longer valid,
        it will select a sprint from the newly selected board. It uses Jira class
        to retrieve available boards and sprints and the hoursManager to
        retrieve the availability and burnupBudget associated with the current
        sprint.
        It emits signals when the available boards or sprints or data of the
        currently selected sprint changes.
    '''

    boardListChanged = QtCore.pyqtSignal(list)
    sprintListChanged = QtCore.pyqtSignal(list)
    selectedSprintChanged = QtCore.pyqtSignal(int, int, int, int)

    def __init__(self, jira, hoursManager, currentBoard, currentSprint):
        super().__init__()

        self.hoursManager = hoursManager
        self.jira = jira

        self.currentBoard = currentBoard
        self.currentSprint = currentSprint
        self.availability = 0
        self.burnupBudget = 0

    def update(self):
        self._updateBoardList()

    def _updateBoardList(self):
        prevBoard = self.currentBoard

        self.boardList = self.jira.getScrumBoards()
        if self.currentBoard not in self.boardList:
            if self.boardList:
                self.currentBoard = sorted(self.boardList.keys())[0]
            else:
                self.currentBoard = None

        self.boardListChanged.emit([(k,v) for k,v in self.boardList.items()])

        self._updateSprintList()

    def _updateSprintList(self):
        if self.currentBoard != None:
            self.sprintList = dict(((sprintId, sprint['name']) for sprintId, sprint in self.jira.getSprints(self.currentBoard).items()))
        else:
            self.sprintList = {}

        if self.currentSprint not in self.sprintList:
            if self.sprintList:
                self.currentSprint = sorted(self.sprintList.keys())[0]
            else:
                self.currentSprint = None

        self.sprintListChanged.emit([(k,v) for k,v in self.sprintList.items()])

        self._updateHours()

    def _updateHours(self):
        self.availability, self.burnupBudget = self.hoursManager.getHours(self.currentBoard, self.currentSprint) if self.currentBoard != None and self.currentSprint != None else (0, 0)
        self.selectedSprintChanged.emit(self.currentBoard, self.currentSprint, self.availability, self.burnupBudget)

    def setBoard(self, boardId):
        if self.currentBoard != boardId:
            self.currentBoard = boardId
            self._updateSprintList()

    def setSprint(self, sprintId):
        if self.currentSprint != sprintId:
            self.currentSprint = sprintId
            self._updateHours()

    def setAvailability(self, availability):
        self.hoursManager.setAvailability(self.currentBoard, self.currentSprint, availability)
        self._updateHours()

    def setBurnupBudget(self, burnupBudget):
        self.hoursManager.setBurnupBudget(self.currentBoard, self.currentSprint, burnupBudget)
        self._updateHours()

def main():
    app = QtGui.QApplication([])

    loadConfiguration()

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('antialias', True)
    
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # There are two ways to use this script without a real Jira server.
    # The first is to have this script read its data from files by setting
    # readFromFile = True when creating an instance of the Jira class.
    # The second is to start up the fakejira.py script and have this script
    # connect to localhost:8080.

    jiraClass = Jira6 if jiraVersion == 6 else Jira7
    jira = jiraClass(config['jiraurl'], readFromFile = False, writeToFile = False)

    hoursManager = HoursManager(config['hours'])
    model = Model(jira, hoursManager, config['currentBoard'], config['currentSprint'])
    gui = Gui(config['jiraurl'], config['username'], '')
    chart = Chart(jira, gui.getPlotWidget().getPlotItem())

    gui.boardChanged.connect(model.setBoard)
    gui.sprintChanged.connect(model.setSprint)
    gui.availabilityChanged.connect(model.setAvailability)
    gui.burnupBudgetChanged.connect(model.setBurnupBudget)

    model.boardListChanged.connect(gui.updateAvailableBoards)
    model.sprintListChanged.connect(gui.updateAvailableSprints)
    model.selectedSprintChanged.connect(gui.updateHours)

    model.selectedSprintChanged.connect(chart.updateChart)

    def reconnect():
        try:
            model.update()
            gui.setConnectionStatus('OK')
            QtCore.QTimer.singleShot(5 * 60 * 1000, reconnect)
        except requests.exceptions.ConnectionError as e:
            gui.setConnectionStatus(str(e))
            gui.openConnectionDialog()
        except requests.exceptions.HTTPError as e:
            gui.setConnectionStatus(str(e))
            status_code = e.response.status_code
            if status_code == 401:
                gui.openConnectionDialog()
            elif status_code == 404:
                QtCore.QTimer.singleShot(5000, reconnect)
            else:
                raise
                
    def connect(jiraUrl, username, password):
        jira.setConnectionData(jiraUrl, username, password)
        reconnect()
    
    gui.connectionDataChanged.connect(connect, QtCore.Qt.QueuedConnection)
    
    gui.openConnectionDialog()
    
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

    config['jiraurl'] = jira.url
    config['username'] = jira.auth[0]
    config['hours'] = hoursManager.hours
    config['currentBoard'] = model.currentBoard
    config['currentSprint'] = model.currentSprint

    saveConfiguration()

if __name__ == '__main__':
    main()
