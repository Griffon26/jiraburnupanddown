#!/usr/bin/python

import copy
import datetime as dt
from dateutil import parser
import json
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pytz
import numpy as np
import tzlocal

jiraVersion = 6

logging = False
write = False
read = True


def log(msg):
    print(msg)


def timestamp_to_seconds(timestamp):
    epoch = dt.datetime.fromtimestamp(0, pytz.utc)
    print(timestamp, epoch)
    return (timestamp - epoch).total_seconds()

def x_timestamps_to_seconds(x_y_data):
    return [[timestamp_to_seconds(x), y] for x, y in x_y_data]

def x_timestamps_to_seconds_np(x_y_data):
    return np.array([[timestamp_to_seconds(x), y] for x, y in x_y_data])

def getSprintDates(sprints, sprintId):
    if jiraVersion == 6:
        dates = jiraREST6_getSprintDates(boardId, sprintId)
        sprintStart = dates['start']
        sprintEnd = dates['end']
    else:
        sprintStart = parser.parse(sprints[sprintId]['startDate'])
        sprintEnd = parser.parse(sprints[sprintId]['endDate'])

    return sprintStart, sprintEnd

def jiraREST6_getScrumBoards():
    '''
  {
    var boards = {};
    var data;

    if(read)
    {
      data = JSON.parse(fs.readFileSync('getScrumBoards.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/greenhopper/1.0/xboard/selectorData',
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getScrumBoards.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }
    $.each(data.rapidViews, function(index, object)
    {
      if(object.sprintSupportEnabled)
      {
        boards[object.id] = object.name;
      }
    });

    return boards;
  }
  '''
    if read:
        with open('jira6/getScrumBoards.json', 'rt') as f:
            jsonData = json.loads(f.read())
    else:
        TODO # implement HTTP request

    boards = {}
    for board in jsonData['rapidViews']:
        if board['sprintSupportEnabled']:
            boards[board['id']] = board['name']

    return boards

def jiraREST7_getScrumBoards():
    '''
  {
    var boards = {};
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board',
      data: { 'startAt' : 0,
              'maxResults' : 1000,
              'type' : 'scrum' },
      success: function(jsonData) {
        $.each(jsonData.values, function(index, object)
        {
          boards[object.id] = object.name;
        });
      },
      error: function(req, textStatus, errorThrown) {
        alert('Error:' + errorThrown);
      }
    });

    return boards;
  }
    '''
    if read:
        with open('getScrumBoards.json', 'rt') as f:
            jsonData = json.loads(f.read())
    else:
        TODO # implement HTTP request

    boards = {}
    for board in jsonData['values']:
        boards[board['id']] = board['name']

    return boards

def jiraREST6_getKanbanBoards():
    '''
  {
    var boards = {};
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getKanbanBoards.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/greenhopper/1.0/xboard/selectorData',
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getKanbanBoards.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }
    $.each(data.rapidViews, function(index, object)
    {
      if(!object.sprintSupportEnabled)
      {
        boards[object.id] = object.name;
      }
    });

    return boards;
  }
    '''
    pass

def jiraREST7_getKanbanBoards():
    '''
  {
    var boards = {};
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board',
      data: { 'startAt' : 0,
              'maxResults' : 1000,
              'type' : 'kanban' },
      success: function(jsonData) {
        $.each(jsonData.values, function(index, object)
        {
          boards[object.id] = object.name;
        });
      },
      error: function(req, textStatus, errorThrown) {
        alert('Error:' + errorThrown);
      }
    });

    return boards;
  }
    '''
    pass

def jiraREST6_getSprints(boardId):
    '''
  {
    var sprints = {};
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getSprints.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/greenhopper/1.0/sprintquery/' + boardId,
        data: { 'startAt' : 0,
                'maxResults' : 1000 },
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getSprints.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }
    $.each(data.sprints, function(index, object)
    {
      sprints[object.id] = object;
    });

    return sprints;
  }
    '''
    with open('jira6/getSprints.json', 'rt') as f:
        jsonData = json.loads(f.read())

    sprints = {}
    for sprint in jsonData['sprints']:
        sprints[sprint['id']] = sprint

    return sprints

def jiraREST6_getSprintDates(boardId, sprintId):
    '''
  {
    var dates = {}
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getSprintDates.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/greenhopper/1.0/rapid/charts/sprintreport',
        data: { 'rapidViewId' : boardId,
                'sprintId' : sprintId },
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getSprintDates.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }
    var endDate = (data.sprint.completeDate != 'None') ? data.sprint.completeDate : data.sprint.endDate;

    dates.start = moment(data.sprint.startDate, 'DD/MMM/YYYY h:mm a');
    dates.end = moment(endDate, 'DD/MMM/YYYY h:mm a');

    return dates;
  }
    '''
    with open('jira6/getSprintDates.json', 'rt') as f:
        jsonData = json.loads(f.read())

    endDate = jsonData['sprint']['completeDate']
    if endDate == 'None':
        endDate = jsonData['sprint']['endDate']

    localzone = tzlocal.get_localzone()
    
    dates = {}
    dates['start'] = localzone.localize(parser.parse(jsonData['sprint']['startDate']))
    dates['end'] = localzone.localize(parser.parse(endDate))

    return dates

def jiraREST7_getSprints(boardId):
    '''
  {
    var sprints = {};
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board/' + boardId + '/sprint',
      data: { 'startAt' : 0,
              'maxResults' : 1000 },
      success: function(jsonData) {
        $.each(jsonData.values, function(index, object)
        {
          sprints[object.id] = object;
        });
      },
      error: function(req, textStatus, errorThrown) {
        alert('Error:' + errorThrown);
      }
    });

    return sprints;
  }
    '''
    with open('getSprints.json', 'rt') as f:
        jsonData = json.loads(f.read())

    sprints = {}
    for sprint in jsonData['values']:
        sprints[sprint['id']] = sprint

    return sprints

def jiraREST6_getIssues(boardId, sprintId) :
    '''
  {
    var issues;
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getIssues.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/api/2/search',
        data: { 'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'issuetype = Sub-task and sprint = ' + sprintId,
                'fields' : 'timetracking,resolutiondate'},
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getIssues.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }
    issues = data.issues;

    return issues;
  }
    '''
    with open('jira6/getIssues.json', 'rt') as f:
        jsonData = json.loads(f.read())

    return jsonData['issues']

def jiraREST7_getIssues(boardId, sprintId):
    '''
  {
    var issues;
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board/' + boardId + '/sprint/' + sprintId + '/issue',
      data: { 'startAt' : 0,
              'maxResults' : 1000,
              'jql' : 'issuetype = Sub-task',
              'fields' : 'timetracking,resolutiondate'},
      success: function(jsonData) {
        issues = jsonData.issues;
      },
      error: function(req, textStatus, errorThrown) {
        alert('Error:' + errorThrown);
      }
    });

    return issues;
  }
    '''
    with open('getIssues.json', 'rt') as f:
        jsonData = json.loads(f.read())

    return jsonData['issues']

def jiraREST6_getEffortForIssues(boardId, issueNames):
    '''
  {
    var effortForIssues = {}
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getEffortForIssues.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/api/2/search',
        data: { 'startAt' : 0,
                'maxResults' : 1000,
                'jql' : 'issuekey in (' + issueNames.join() + ')',
                'fields' : 'timetracking'},
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getEffortForIssues.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }
    $.each(data.issues, function(index, issue)
    {
      if ('originalEstimateSeconds' in issue.fields.timetracking)
      {
        effortForIssues[issue.key] = issue.fields.timetracking.originalEstimateSeconds;
      }
      else
      {
        effortForIssues[issue.key] = 0;
      }
    });

    return effortForIssues;
  }
    '''
    with open('jira6/getEffortForIssues.json', 'rt') as f:
        jsonData = json.loads(f.read())

    effortForIssues = {}
    for issue in jsonData['issues']:
        if 'originalEstimateSeconds' in issue['fields']['timetracking']:
            effortForIssues[issue['key']] = issue['fields']['timetracking']['originalEstimateSeconds']
        else:
            effortForIssues[issue['key']] = 0

    return effortForIssues

def jiraREST7_getEffortForIssues(boardId, issueNames):
    '''
  {
    var effortForIssues = {}
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board/' + boardId + '/issue',
      data: { 'startAt' : 0,
              'maxResults' : 1000,
              'jql' : 'issuekey in (' + issueNames.join() + ')',
              'fields' : 'timetracking'},
      success: function(jsonData) {
        $.each(jsonData.issues, function(index, issue)
        {
          if ('originalEstimateSeconds' in issue.fields.timetracking)
          {
            effortForIssues[issue.key] = issue.fields.timetracking.originalEstimateSeconds;
          }
          else
          {
            effortForIssues[issue.key] = 0;
          }
        });
      },
      error: function(req, textStatus, errorThrown) {
        alert('Error:' + errorThrown);
      }
    });

    return effortForIssues;
  }
    '''
    with open('getEffortForIssues.json', 'rt') as f:
        jsonData = json.loads(f.read())

    effortForIssues = {}
    for issue in jsonData['issues']:
        if 'originalEstimateSeconds' in issue['fields']['timetracking']:
            effortForIssues[issue['key']] = issue['fields']['timetracking']['originalEstimateSeconds']
        else:
            effortForIssues[issue['key']] = 0

    return effortForIssues

def jiraREST_getScopeChangeBurndownChart(rapidViewId, sprintId):
    '''
  {
    var result;
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getScopeChangeBurndownChart.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/greenhopper/1.0/rapid/charts/scopechangeburndownchart',
        data: { 'rapidViewId' : rapidViewId,
                'sprintId' : sprintId },
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getScopeChangeBurndownChart.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }

    return data;
  }
    '''
    with open('jira6/getScopeChangeBurndownChart.json', 'rt') as f:
        jsonData = json.loads(f.read())

    return jsonData

def jiraREST6_getIssueWorklogs(boardId, sprintStart, sprintEnd):
    '''
  {
    var result;
    var data;
    
    if(read)
    {
      data = JSON.parse(fs.readFileSync('getIssueWorklogs.json'));
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/api/2/search',
        data: { 'startAt' : 0,
                'maxResults' : 1000,
                'jql' : '(resolved >= ' + sprintStart + ' or resolution = unresolved) and (created <= ' + sprintEnd + ') and (updated >= ' + sprintStart + ') and (issuetype = Support)',
                'fields' : 'worklog' },
        success: function(jsonData) {
          if(write)
          {
            fs.writeFileSync('getIssueWorklogs.json', JSON.stringify(jsonData, null, 8));
          }
          data = jsonData;
        },
        error: function(req, textStatus, errorThrown) {
          alert('Error:' + errorThrown);
        }
      });
    }

    return data.issues;
  }
    '''
    with open('jira6/getIssueWorklogs.json', 'rt') as f:
        jsonData = json.loads(f.read())

    return jsonData['issues']

def jiraREST7_getIssueWorklogs(boardId, sprintStart, sprintEnd):
    '''
  {
    var result;
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board/2/issue',
      data: { 'startAt' : 0,
              'maxResults' : 1000,
              'jql' : 'worklogDate >= ' + sprintStart + ' and worklogDate <= ' + sprintEnd + ' and issuetype = Support',
              'fields' : 'worklog' },
      success: function(jsonData) {
        result = jsonData.issues;
      },
      error: function(req, textStatus, errorThrown) {
        alert('Error:' + errorThrown);
      }
    });

    return result;
  }
    '''
    pass

'''
  function popup(object)
  {
    alert(JSON.stringify(object, null, 8));
  }

  function byTimestamp(x, y)
  {
    return x[0].diff(y[0]);
  }
'''

def byResolutionDate(x):
    '''
    var result;

    if(!x.fields.resolutiondate)
    {
      result = 1;
    }
    else if(!y.fields.resolutiondate)
    {
      result = -1;
    }
    else
    {
      result = moment(x.fields.resolutiondate).diff(moment(y.fields.resolutiondate));
    }

    /*
    popup('(' + x.id + ',' + x.fields.resolutiondate + ') ' + ((result < 0) ? '<' :
                                                               (result > 0) ? '>' :
                                                                             '==') + ' (' + y.id + ',' + y.fields.resolutiondate + ')');
    */
    return result;
  }
    '''
    return 0

def createSegments(input, connected):
    '''
  {
    var dataSet = [ input[0] ];
    var previousY = input[0][1];

    $.each(input, function(index, value)
    {
      /* Skip the first element */
      if(index == 0)
      {
        return true;
      }

      dataSet.push([value[0], previousY]);
      if(!connected)
      {
        dataSet.push(null);
      }
      dataSet.push(value);
      previousY = value[1];
    });

    return dataSet;
  }
    '''
    pass

def getZeroData(sprintStart, sprintEnd):
    return [[sprintStart, 0], [sprintEnd, 0]]

def createZeroLine(plotItem, zeroData):
    pen = pg.mkPen('k', width=1, style=QtCore.Qt.DashLine)

    plotItem.plot(x_timestamps_to_seconds_np(zeroData), pen = pen)

def getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart):
    '''
  {
    var timezoneOffset = moment.duration(sprintStart.diff(moment(scopeChangeBurndownChart.startTime)));
    var initialScope = [];
    var scopeChanges = [];

    var tmpSet = {};
    var issueNames = [];
    var alreadyDone = {};

    $.each(scopeChangeBurndownChart.changes, function(timestamp, changelist)
    {
      timestamp = moment(parseInt(timestamp));
      timestamp.add(timezoneOffset);

      $.each(changelist, function(index, change)
      {
        if(change.column != undefined &&
           change.column.done &&
           timestamp <= sprintStart)
        {
          alreadyDone[change.key] = true;
        }
      });
    });

    $.each(scopeChangeBurndownChart.changes, function(timestamp, changelist)
    {
      timestamp = moment(parseInt(timestamp));
      timestamp.add(timezoneOffset);

      $.each(changelist, function(index, change)
      {
        /* Skip parent issues */
        if(!scopeChangeBurndownChart.issueToParentKeys[change.key])
        {
          return true;
        }

        /* Skip changes that are not sprint scope changes */
        if(change.added == undefined)
        {
          return true;
        }

        /* Ignore issues that were already completed before the sprint had started */
        if(change.key in alreadyDone)
        {
          return true;
        }

        /* Choose whether to add it to the initialScope or to the scopeChanges */
        if(timestamp <= sprintStart)
        {
          initialScope.push( { 'timestamp' : timestamp,
                               'added'     : change.added,
                               'issueName' : change.key } );
        }
        else if(timestamp <= sprintEnd)
        {
          scopeChanges.push( { 'timestamp' : timestamp,
                               'added'     : change.added,
                               'issueName' : change.key } );
        }

        if(!(change.key in tmpSet))
        {
          tmpSet[change.key] = true;
          issueNames.push(change.key);
        }
      });
    });

    return { 'names' : issueNames,
             'initial' : initialScope,
             'changes' : scopeChanges };
  }
    '''
    return { 'names' : [],
             'initial' : [],
             'changes' : [] }

def getInitialScope(initialIssues, effortForIssues):
    '''
  {
    var initialScope = 0;

    log('Calculating initial sprint scope');

    $.each(initialIssues, function(index, issue)
    {
      var effort = effortForIssues[issue.issueName] / 3600;
      initialScope += effort;
      log("  adding " + issue.issueName + ": " + effort + " hours");
    });

    log("  Initial sprint scope is " + initialScope + " hours");

    return initialScope;
  }
    '''
    return 0

def calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues, effortForIssues):
    '''
  {
    var scope = 0;
    var scopeChanges = [];

    log('Calculating sprint scope changes');

    scopeChanges.push( [ sprintStart.clone(), 0 ] );

    $.each(scopeChangingIssues, function(index, scopeChange)
    {
      var effort = effortForIssues[scopeChange.issueName] / 3600;

      if(scopeChange.added)
      {
        scope += effort;
        log('  added ' + scopeChange.issueName + ': ' + effort + ' hours');
      }
      else
      {
        scope -= effort;
        log('  removed ' + scopeChange.issueName + ': ' + effort + ' hours');
      }

      scopeChanges.push( [ scopeChange.timestamp.clone(), scope ] );
    });

    log('  Overall scope change: ' + scope + ' hours');

    scopeChanges.push( [ sprintEnd.clone(), scope ] );

    return scopeChanges;
  }
    '''
    return [ (0, 0) ]

def createSprintScopeLine(plotItem, data):
    '''
  {
    var endScope = data[data.length - 1][1];
    var lineData = []

    $.each(data, function(index, value)
    {
      lineData.push([value[0], endScope - value[1]]);
    });

    return { 'color' : 'black',
             'data'  : createSegments(lineData, true) };
  }
    '''
    pass

def getIdealBurndown(sprintStart, sprintEnd, finalSprintScope):
    '''
  {
    return [ [sprintStart.clone(), finalSprintScope], [sprintEnd.clone(), 0] ];
  }
    '''
    pass

def createIdealBurndownLine(plotItem, idealBurndownData):
    '''
  {
    return { 'color' : '#c0c0c0',
             'data' : idealBurndownData };
  }
    '''
    pass

def getActualBurndown(sprintStart, sprintEnd, finalSprintScope, issues):
    '''
  {
    var remainingSprintEffort = finalSprintScope;
    var actual = [ [sprintStart, remainingSprintEffort] ]

    $.each(issues, function(index, value)
    {
      if(value.fields.resolutiondate)
      {
        var resolutionDate = moment(value.fields.resolutiondate);
        if(resolutionDate >= sprintStart &&
           resolutionDate <= sprintEnd)
        {
          if(value.fields.timetracking.originalEstimateSeconds)
          {
            remainingSprintEffort -= value.fields.timetracking.originalEstimateSeconds / 3600;
            actual.push([resolutionDate, remainingSprintEffort]);
          }
        }
      }
      else
      {
        return false;
      }
    });

    var currentDate = moment();
    var lastDate = (currentDate < sprintEnd) ? currentDate : sprintEnd;

    actual.push([lastDate.clone(), remainingSprintEffort]);

    return actual;
  }
    '''
    pass

def createActualBurndownLine(plotItem, actualBurndownData):
    '''
  {
    return { 'color' : 'blue',
             'data'  : createSegments(actualBurndownData, true) };
  }
    '''
    pass

def adjustForHiddenWeekends(points, weekends):
    '''
  {
    var weekendIndex = 0;
    var pointIndex = 0;

    var accumulatedOffset = moment.duration(0);

    while(pointIndex < points.length)
    {
      var nextWeekend = weekends[weekendIndex];
      var nextPoint = points[pointIndex];

      /*
      popup({ 'nextPoint' : nextPoint,
              'nextWeekend' : nextWeekend,
              'points' : points,
              'weekends' : weekends,
              'accum' : accumulatedOffset.humanize() });
              */

      if(nextWeekend != undefined && nextPoint[0] > nextWeekend.start)
      {
        if(nextPoint[0] > nextWeekend.start.clone().add(nextWeekend.duration))
        {
          accumulatedOffset.add(nextWeekend.duration);
          weekendIndex++;
        }
        else
        {
          nextPoint[0] = nextWeekend.start.clone().subtract(accumulatedOffset);
          pointIndex++;
        }
      }
      else
      {
        nextPoint[0].subtract(accumulatedOffset);
        pointIndex++;
      }
    }
    /*
    popup({ 'points' : points,
            'weekends' : weekends,
            'accum' : accumulatedOffset.humanize() });
            */
  }
    '''
    return points

def determineSprintWeekends(sprintStart, sprintEnd):
    '''
  {
    var endOfWeek = sprintStart.clone().endOf('isoweek');
    var startOfWeekend = endOfWeek.clone().subtract(2, 'days');
    var weekends = [];

    while(startOfWeekend < sprintEnd)
    {
      var startOfNonWork = moment.max(sprintStart, startOfWeekend);
      var endOfNonWork = moment.min(sprintEnd, endOfWeek);

      weekends.push( { 'start' : startOfNonWork,
                       'duration' : moment.duration(endOfNonWork.diff(startOfNonWork)) } );

      endOfWeek.add(1, 'weeks');
      startOfWeekend = endOfWeek.clone().subtract(2, 'days');
    }
    return weekends;
  }
    '''
    pass

def createDayLabels(sprintStart, sprintEnd):
    '''
  {
    var labels = [];
    var day = sprintStart.clone().hours(12).minutes(0).seconds(0).milliseconds(0);
    if(day < sprintStart)
    {
      day.add(1, 'day');
    }
    while(day < sprintEnd)
    {
      if([6,7].indexOf(day.isoWeekday()) == -1)
      {
        labels.push([day.clone(), day.format('ddd')]);
      }
      day.add(1, 'day');
    }
    return labels;
  }
    '''
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
    '''
  {
    var lines = [];
    var day = sprintStart.clone().hours(0).minutes(0).seconds(0).milliseconds(0);
    if(day < sprintStart)
    {
      day.add(1, 'day');
    }
    while(day < sprintEnd)
    {
      if([6,7].indexOf(day.isoWeekday()) == -1)
      {
        lines.push([day.clone(), undefined]);
      }
      day.add(1, 'day');
    }
    return lines;
  }
    '''
    pass

def createGridLineMarkings(plotItem, gridData):
    '''
  {
    var markings = [];
    $.each(gridData, function(index, value)
    {
      markings.push( { xaxis: { from: value[0], to: value[0] } } );
    });

    return markings;
  }
    '''
    pass

def calculateActualBurnup(sprintStart, sprintEnd, issueWorklogs, burnupBudget, pointsPerHour):
    '''
  {
    var totalHoursIn = 0;
    var totalHoursOut = 0;
    var timeSpent = []

    log('Calculating support burnup');

    $.each(issueWorklogs, function(i, issue)
    {
      $.each(issue.fields.worklog.worklogs, function(j, worklog)
      {
        var created = moment(worklog.created);
        if(created >= sprintStart && created <= sprintEnd)
        {
          timeSpent.push([created, worklog.timeSpentSeconds]);
          totalHoursIn += worklog.timeSpentSeconds / 3600;
          log('  adding ' + issue.key + ': ' + (worklog.timeSpentSeconds / 3600) + ' hours');
        }
        else
        {
          totalHoursOut += worklog.timeSpentSeconds / 3600;
          log('  skipping ' + issue.key + ': ' + (worklog.timeSpentSeconds / 3600) + ' hours');
        }
      });
    });

    log('  Added a total of ' + totalHoursIn + ' hours from worklogs');
    log('  Skipped a total of ' + totalHoursOut + ' hours from worklogs');

    timeSpent.sort(byTimestamp);

    var totalTimeSpent = 0;
    var burnup = [ [sprintStart, -burnupBudget * pointsPerHour] ];
    $.each(timeSpent, function(i, timeSpent)
    {
      totalTimeSpent += timeSpent[1];
      burnup.push([timeSpent[0], ((totalTimeSpent / 3600) - burnupBudget) * pointsPerHour]);
    });
    var currentDate = moment();
    var lastDate = (currentDate < sprintEnd) ? currentDate : sprintEnd;
    burnup.push([lastDate.clone(), ((totalTimeSpent / 3600) - burnupBudget) * pointsPerHour]);

    return burnup;
  }
    '''
    pass

def createActualBurnupLine(plotItem, actualBurnupData):
    '''
  {
    return { 'color' : 'red',
             'data'  : createSegments(actualBurnupData, true) };
  }
    '''
    pass

# This function is a bit different because it calculates data from a line
# from which the weekends have already been removed. This makes it easier to
# calculate the slope of the projected burnup.
def calculateProjectedBurnup(zeroData, actualBurnupData):
    '''
  {
    var burnupStart = actualBurnupData[0][0];
    var burnupStartHeight = actualBurnupData[0][1];
    var burnupEnd = actualBurnupData[actualBurnupData.length - 1][0];
    var burnupEndHeight = actualBurnupData[actualBurnupData.length - 1][1];

    var sprintStart = zeroData[0][0];
    var sprintEnd = zeroData[zeroData.length - 1][0];

    var projectedBurnupHeight = ((burnupEndHeight - burnupStartHeight) / burnupEnd.diff(burnupStart)) * sprintEnd.diff(sprintStart) + burnupStartHeight;

    return [ [burnupEnd.clone(), burnupEndHeight], [sprintEnd.clone(), projectedBurnupHeight] ];
  }
    '''
    return [ (0, 0), (0, 0) ]

def createProjectedBurnupLine(plotItem, projectedBurnupData):
    '''
  {
    return { color: 'red',
             dashes : { show: true, lineWidth : 1 },
             data : projectedBurnupData };
  }
    '''
    pass

def calculateIdealBurnup(sprintStart, sprintEnd, burnupBudget):
    '''
  {
    return [ [sprintStart.clone(), -burnupBudget], [sprintEnd.clone(), 0] ];
  }
    '''
    pass

def createIdealBurnupLine(plotItem, idealBurnupData):
    '''
  {
    return { color: '#c0c0c0',
             data : idealBurnupData }
  }
    '''
    pass

def calculateExpectedBurndown(sprintStart, sprintEnd, finalSprintScope, projectedBurnupHeight):
    '''
  {
    if(projectedBurnupHeight < 0)
    {
      return [ [sprintStart.clone(), finalSprintScope], [sprintEnd.clone(), projectedBurnupHeight] ];
    }
    else
    {
      return [];
    }
  }
    '''
    pass

def createExpectedBurndownLine(plotItem, expectedBurndownData):
    '''
  {
    return { color: 'green',
             data : expectedBurndownData };
  }
    '''
    pass

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

def updateChart(plotItem, sprints, boardId, supportBoardId, sprintId, burnupBudget, availability):
    #
    # Gather all data
    #
    sprintStart, sprintEnd = getSprintDates(sprints, sprintId)

    log("Sprint start is %s" % sprintStart)
    log("Sprint end   is %s" % sprintEnd)

    weekends = determineSprintWeekends(sprintStart, sprintEnd)

    zeroData = getZeroData(sprintStart, sprintEnd)
    axisData = createDayLabels(sprintStart, sprintEnd)
    gridData = createDayLines(sprintStart, sprintEnd)


    # Burndown
    scopeChangeBurndownChart = jiraREST_getScopeChangeBurndownChart(boardId, sprintId)
    scopeChangingIssues = getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart)
    effortForIssues = jiraREST6_getEffortForIssues(boardId, scopeChangingIssues['names']) if (jiraVersion == 6) else \
                      jiraREST7_getEffortForIssues(boardId, scopeChangingIssues['names'])
    sprintScopeData = calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues['changes'], effortForIssues)

    initialSprintScope = getInitialScope(scopeChangingIssues['initial'], effortForIssues)
    finalSprintScope = initialSprintScope + sprintScopeData[-1][1]

    idealBurndownData = getIdealBurndown(sprintStart, sprintEnd, finalSprintScope)

    issues = jiraREST6_getIssues(boardId, sprintId) if (jiraVersion == 6) else \
             jiraREST7_getIssues(boardId, sprintId)
    issues.sort(key=byResolutionDate)
    actualBurndownData = getActualBurndown(sprintStart, sprintEnd, finalSprintScope, issues)


    # Burnup

    pointsPerHour = initialSprintScope / (availability - burnupBudget)

    issueWorklogs = jiraREST6_getIssueWorklogs(supportBoardId, sprintStart, sprintEnd) if (jiraVersion == 6) else \
                    jiraREST7_getIssueWorklogs(supportBoardId, sprintStart, sprintEnd)
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

    now = dt.datetime.now()

    plotItem.getAxis('bottom').setTicks([x_timestamps_to_seconds(axisData)])
    plotItem.setYRange(-burnupBudget * pointsPerHour, finalSprintScope)

    createZeroLine(plotItem, zeroData)
    createSprintScopeLine(plotItem, sprintScopeData)
    createIdealBurndownLine(plotItem, idealBurndownData)
    createActualBurndownLine(plotItem, actualBurndownData)
    createGridLineMarkings(plotItem, gridData)
    createActualBurnupLine(plotItem, actualBurnupData)
    createProjectedBurnupLine(plotItem, projectedBurnupData)
    createIdealBurnupLine(plotItem, idealBurnupData)
    createExpectedBurndownLine(plotItem, expectedBurndownData)

    annotateBudgetOverrun(plotItem, zeroData[-1][0], projectedBurnupHeight)

def initializePlot(plotItem):
    plotItem.showGrid(True, True, 0.3)

if __name__ == '__main__':
    app = QtGui.QApplication([])

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

    boards = jiraREST6_getScrumBoards() if (jiraVersion == 6) else \
             jiraREST7_getScrumBoards()
    print('All available board IDs are: %s' % boards)
    boardId = 8
    sprints = jiraREST6_getSprints(boardId) if (jiraVersion == 6) else \
              jiraREST7_getSprints(boardId)
    sprintId = 533
    print('All available sprints for board %s are: %s' % (boardId, sprints))
    updateChart(pi, sprints, boardId, None, sprintId, 100, 500)

    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

