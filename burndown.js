
window.$ = window.jQuery = require('jquery');

require('flot');
moment = require('moment');
require('./jquery.flot.dashes.js');
fs = require('fs');
ipc = require('ipc');

var jiraurl = localStorage.getItem('jiraurl');
var jiraVersion = 6;

$(function() {

  var settings = ipc.sendSync('get_settings');

  function log(s)
  {
    if(settings.logging)
    {
      fs.appendFileSync('burndown.log', s + '\n');
    }
  }

  function jiraREST6_getScrumBoards() 
  {
    var boards = {};
    var data;

    if(settings.read)
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
          if(settings.write)
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

  function jiraREST7_getScrumBoards() 
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

  function jiraREST6_getKanbanBoards() 
  {
    var boards = {};
    var data;
    
    if(settings.read)
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
          if(settings.write)
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

  function jiraREST7_getKanbanBoards() 
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

  function jiraREST6_getSprints(boardId) 
  {
    var sprints = {};
    var data;
    
    if(settings.read)
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
          if(settings.write)
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

  function jiraREST6_getSprintDates(boardId, sprintId) 
  {
    var dates = {}
    var data;
    
    if(settings.read)
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
          if(settings.write)
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

  function jiraREST7_getSprints(boardId) 
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

  function jiraREST6_getIssues(boardId, sprintId) 
  {
    var issues;
    var data;
    
    if(settings.read)
    {
      try {
        data = JSON.parse(fs.readFileSync('getIssues.json'));
      } catch(e) {
        alert('Failed to read from getIssues.json. Please get the data from:\n' +
              '/rest/api/2/search?jql=issuetype = Sub-task and sprint = ' + sprintId + '&fields=timetracking,resolutiondate');
        throw e;
      }
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
          if(settings.write)
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

  function jiraREST7_getIssues(boardId, sprintId) 
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

  function jiraREST6_getEffortForIssues(boardId, issueNames)
  {
    var effortForIssues = {}
    var data;
    
    if(settings.read)
    {
      try {
        data = JSON.parse(fs.readFileSync('getEffortForIssues.json'));
      } catch (e) {
        alert('Failed to read from getEffortForIssues.json. Please get the data from:\n/rest/api/2/search?jql=issuekey in (' + issueNames.join() + ')&fields=timetracking\n');
        throw e;
      }
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
          if(settings.write)
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

  function jiraREST7_getEffortForIssues(boardId, issueNames)
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

  function jiraREST_getScopeChangeBurndownChart(rapidViewId, sprintId)
  {
    var result;
    var data;
    
    if(settings.read)
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
          if(settings.write)
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

  function jiraREST6_getIssueWorklogs(boardId, sprintStart, sprintEnd)
  {
    var result;
    var data;
    var jql = '(resolved >= ' + sprintStart + ' or resolution = unresolved) and ' +
              '(created <= ' + sprintEnd + ') and (updated >= ' + sprintStart + ') and ' +
              '(issuetype in ("Support", "Incident", "Baseline tracking & qualification")) and ' +
              '(summary !~ "Team Activities")';
    
    if(settings.read)
    {
      try {
        data = JSON.parse(fs.readFileSync('getIssueWorklogs.json'));
      } catch(e) {
        alert('Failed to read from getIssueWorklogs.json. Please get the data from:\n' +
              '/rest/api/2/search?jql=' + jql.replace(' & ', ' %26 ') + '&fields=worklog\n');
        throw(e)
      }
    }
    else
    {
      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/api/2/search',
        data: { 'startAt' : 0,
                'maxResults' : 1000,
                'jql' : jql,
                'fields' : 'worklog' },
        success: function(jsonData) {
          if(settings.write)
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

  function jiraREST7_getIssueWorklogs(boardId, sprintStart, sprintEnd)
  {
    var result;
    
    $.ajax({
      async: false,
      type: 'GET',
      url: jiraurl + '/rest/agile/1.0/board/2/issue',
      data: { 'startAt' : 0,
              'maxResults' : 1000,
              'jql' : '(worklogDate >= ' + sprintStart + ') and (worklogDate <= ' + sprintEnd + ') and ' +
                      '(issuetype in ("Support", "Incident", "Baseline tracking & qualification")) and ' +
                      '(summary !~ "Team Activities")',
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

  function popup(object)
  {
    alert(JSON.stringify(object, null, 8));
  }

  function byTimestamp(x, y)
  {
    return x[0].diff(y[0]);
  }

  function byResolutionDate(x, y)
  {
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

  function createSegments(input, connected)
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

  function getZeroData(sprintStart, sprintEnd)
  {
    return [ [sprintStart.clone(), 0],
             [sprintEnd.clone(), 0] ];
  }

  function createZeroLine(zeroData)
  {
    return { 'color'  : 'black',
             'dashes' : { 'show' : true,
                          'lineWidth' : 1 },
             'data'   : zeroData };
  }

  function getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart)
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

  function getInitialScope(initialIssues, effortForIssues)
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

  function calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues, effortForIssues)
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

  function createSprintScopeLine(data)
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

  function getIdealBurndown(sprintStart, sprintEnd, finalSprintScope)
  {
    return [ [sprintStart.clone(), finalSprintScope], [sprintEnd.clone(), 0] ];
  }

  function createIdealBurndownLine(idealBurndownData)
  {
    return { 'color' : '#c0c0c0',
             'data' : idealBurndownData };
  }

  function getActualBurndown(sprintStart, sprintEnd, finalSprintScope, issues)
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

  function createActualBurndownLine(actualBurndownData)
  {
    return { 'color' : 'blue',
             'data'  : createSegments(actualBurndownData, true) };
  }

  function adjustForHiddenWeekends(points, weekends)
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

  function determineSprintWeekends(sprintStart, sprintEnd)
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

  function createDayLabels(sprintStart, sprintEnd)
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

  function createDayLines(sprintStart, sprintEnd)
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

  function createGridLineMarkings(gridData)
  {
    var markings = [];
    $.each(gridData, function(index, value)
    {
      markings.push( { xaxis: { from: value[0], to: value[0] } } );
    });

    return markings;
  }

  function calculateActualBurnup(sprintStart, sprintEnd, issueWorklogs, burnupBudget, pointsPerHour)
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

  function createActualBurnupLine(actualBurnupData)
  {
    return { 'color' : 'red',
             'data'  : createSegments(actualBurnupData, true) };
  }

  /* This function is a bit different because it calculates data from a line
   * from which the weekends have already been removed. This makes it easier to
   * calculate the slope of the projected burnup.
   */
  function calculateProjectedBurnup(zeroData, actualBurnupData)
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

  function createProjectedBurnupLine(projectedBurnupData)
  {
    return { color: 'red',
             dashes : { show: true, lineWidth : 1 },
             data : projectedBurnupData };
  }

  function calculateIdealBurnup(sprintStart, sprintEnd, burnupBudget)
  {
    return [ [sprintStart.clone(), -burnupBudget], [sprintEnd.clone(), 0] ];
  }

  function createIdealBurnupLine(idealBurnupData)
  {
    return { color: '#c0c0c0',
             data : idealBurnupData }
  }

  function calculateExpectedBurndown(sprintStart, sprintEnd, finalSprintScope, projectedBurnupHeight)
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

  function createExpectedBurndownLine(expectedBurndownData)
  {
    return { color: 'green',
             data : expectedBurndownData };
  }

  function annotateBudgetOverrun(plot, max_x, projectedBurnupHeight)
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

  function updateChart(boardId, supportBoardId, sprintId, burnupBudget, availability)
  {
    /*
     * Gather all data
     */

    if(jiraVersion == 6)
    {
      var dates = jiraREST6_getSprintDates(boardId, sprintId);
      var sprintStart = dates.start;
      var sprintEnd = dates.end;
    }
    else
    {
      var sprintStart = moment(new Date(sprints[sprintId].startDate));
      var sprintEnd = moment(new Date(sprints[sprintId].endDate));
    }

    log("Sprint start is " + sprintStart.format());
    log("Sprint end   is " + sprintEnd.format());

    var weekends = determineSprintWeekends(sprintStart, sprintEnd);

    var zeroData = getZeroData(sprintStart, sprintEnd);
    var axisData = createDayLabels(sprintStart, sprintEnd);
    var gridData = createDayLines(sprintStart, sprintEnd);


    /* Burndown */
    var scopeChangeBurndownChart = jiraREST_getScopeChangeBurndownChart(boardId, sprintId);
    var scopeChangingIssues = getScopeChangingIssues(sprintStart, sprintEnd, scopeChangeBurndownChart);
    var effortForIssues = (jiraVersion == 6) ?
                            jiraREST6_getEffortForIssues(boardId, scopeChangingIssues.names) :
                            jiraREST7_getEffortForIssues(boardId, scopeChangingIssues.names);
    var sprintScopeData = calculateScopeChanges(sprintStart, sprintEnd, scopeChangingIssues.changes, effortForIssues);

    var initialSprintScope = getInitialScope(scopeChangingIssues.initial, effortForIssues);
    var finalSprintScope = initialSprintScope + sprintScopeData[sprintScopeData.length - 1][1];

    var idealBurndownData = getIdealBurndown(sprintStart, sprintEnd, finalSprintScope);

    var issues = (jiraVersion == 6) ?
                   jiraREST6_getIssues(boardId, sprintId) :
                   jiraREST7_getIssues(boardId, sprintId);
    issues.sort(byResolutionDate);
    var actualBurndownData = getActualBurndown(sprintStart, sprintEnd, finalSprintScope, issues);


    /* Burnup */

    var pointsPerHour = initialSprintScope / (availability - burnupBudget);

    var issueWorklogs = (jiraVersion == 6) ? 
                          jiraREST6_getIssueWorklogs(supportBoardId, sprintStart, sprintEnd) :
                          jiraREST7_getIssueWorklogs(supportBoardId, sprintStart, sprintEnd);
    var actualBurnupData = calculateActualBurnup(sprintStart, sprintEnd, issueWorklogs, burnupBudget, pointsPerHour);

    var idealBurnupData = calculateIdealBurnup(sprintStart, sprintEnd, burnupBudget * pointsPerHour);



    /*
     * Remove all weekends
     */
    adjustForHiddenWeekends(zeroData, weekends);
    adjustForHiddenWeekends(sprintScopeData, weekends);
    adjustForHiddenWeekends(idealBurndownData, weekends);
    adjustForHiddenWeekends(actualBurndownData, weekends);
    adjustForHiddenWeekends(axisData, weekends);
    adjustForHiddenWeekends(gridData, weekends);
    adjustForHiddenWeekends(actualBurnupData, weekends);
    adjustForHiddenWeekends(idealBurnupData, weekends);

    var projectedBurnupData = calculateProjectedBurnup(zeroData, actualBurnupData);

    var projectedBurnupHeight = projectedBurnupData[projectedBurnupData.length - 1][1];
    var expectedBurndownData = calculateExpectedBurndown(sprintStart, sprintEnd, finalSprintScope, projectedBurnupHeight);
    adjustForHiddenWeekends(expectedBurndownData, weekends);

    /*
     * Turn it into plottable data
     */
    var zero = createZeroLine(zeroData);
    var scope = createSprintScopeLine(sprintScopeData);
    var idealBurndown = createIdealBurndownLine(idealBurndownData);
    var actualBurndown = createActualBurndownLine(actualBurndownData);
    var gridLines = createGridLineMarkings(gridData);
    var actualBurnup = createActualBurnupLine(actualBurnupData);
    var projectedBurnup = createProjectedBurnupLine(projectedBurnupData);
    var idealBurnup = createIdealBurnupLine(idealBurnupData);
    var expectedBurndown = createExpectedBurndownLine(expectedBurndownData);



    /*
     * Plot
     */

    var now = moment();

    var options = {
      grid : { borderWidth : 0,
               margin: { 'top' : 0,
                         'left' : 0,
                         'right' : 60,
                         'bottom' : 0 },
               markings: gridLines },
      xaxis : { ticks : axisData,
                tickLength : 0 },
      yaxis : { min : -burnupBudget * pointsPerHour, max: finalSprintScope },
      series : {
        shadowSize: 0,
        }
    }
    var plot = $.plot("#placeholder", [ idealBurnup,
                                        idealBurndown,
                                        zero,
                                        scope,
                                        actualBurndown,
                                        actualBurnup,
                                        projectedBurnup,
                                        expectedBurndown ], options);

    annotateBudgetOverrun(plot, zeroData[zeroData.length - 1][0], projectedBurnupHeight);

  }

  function getSelectedBoardId()
  {
    return $('#boardSelection').val();
  }
  function getSelectedSupportBoardId()
  {
    return $('#supportBoardSelection').val();
  }
  function getSelectedSprintId()
  {
    return $('#sprintSelection').val();
  }
  function getBurnupBudgetField()
  {
    return $('#burnupBudget').val();
  }
  function setBurnupBudgetField(value)
  {
    $('#burnupBudget').val(value);
  }
  function getAvailabilityField()
  {
    return $('#availability').val();
  }
  function setAvailabilityField(value)
  {
    $('#availability').val(value);
  }

  function main()
  {
    var options = [];
    var boards = (jiraVersion == 6) ?
                   jiraREST6_getScrumBoards() :
                   jiraREST7_getScrumBoards();
    $.each(boards, function(key, value)
    {
        options.push('<option value="'+ key +'">'+ value +'</option>');
    });
    $('#boardSelection').html(options.join(''));

    options = [];
    var boards = (jiraVersion == 6) ?
                   jiraREST6_getKanbanBoards() :
                   jiraREST7_getKanbanBoards();
    $.each(boards, function(key, value)
    {
        options.push('<option value="'+ key +'">'+ value +'</option>');
    });
    $('#supportBoardSelection').html(options.join(''));

    updateSprintSelectionIfPossible();

    var lastSelectedBoardId = localStorage.getItem('last_selected_board');
    var lastSelectedSupportBoardId = localStorage.getItem('last_selected_support_board');
    var lastSelectedSprintId = localStorage.getItem('last_selected_sprint');

    if(lastSelectedBoardId != undefined)
    {
      $('#boardSelection').val(lastSelectedBoardId);
      if(lastSelectedSprintId != undefined)
      {
        $('#sprintSelection').val(lastSelectedSprintId);
      }
    }
    if(lastSelectedSupportBoardId != undefined) 
    {
      $('#boardSelection').val(lastSelectedBoardId);
    }

    updateChartIfPossible();
    setInterval(updateChartIfPossible, 5 * 60 * 1000);
  }

  function updateSprintSelectionIfPossible()
  {
    var boardId = getSelectedBoardId();

    if(boardId != undefined)
    {
      var options = [];
      var sprints = (jiraVersion == 6) ? 
                      jiraREST6_getSprints(boardId) :
                      jiraREST7_getSprints(boardId);
      $.each(sprints, function(key, value)
      {
          options.push('<option value="'+ key +'">'+ value.name +'</option>');
      });
      $('#sprintSelection').html(options.join(''));
    }
  }

  function updateChartIfPossible()
  {
    var boardId = getSelectedBoardId();
    var supportBoardId = getSelectedSupportBoardId();
    var sprintId = getSelectedSprintId();
    var availability;
    var burnupBudget;

    localStorage.setItem('last_selected_board', boardId);
    localStorage.setItem('last_selected_support_board', supportBoardId);
    localStorage.setItem('last_selected_sprint', sprintId);

    if(sprintId != undefined)
    {
      availability = localStorage.getItem('availability_sprint_' + sprintId);
      if(availability == undefined)
      {
        availability = 1;
      }
      setAvailabilityField(availability);

      burnupBudget = localStorage.getItem('budget_sprint_' + sprintId);
      if(burnupBudget == undefined)
      {
        burnupBudget = 0;
      }
      setBurnupBudgetField(burnupBudget);
    }

    if(boardId != undefined &&
       supportBoardId != undefined &&
       sprintId != undefined &&
       burnupBudget != undefined &&
       availability != undefined)
    {
      log('\n========== Redrawing chart for sprint ' + sprintId + ' ===========');
      updateChart(boardId, supportBoardId, sprintId, burnupBudget, availability);
    }
  }

  $('#boardSelection').change(function() {
    updateSprintSelectionIfPossible();
    updateChartIfPossible();
  });

  $('#supportBoardSelection').change(function() {
    updateChartIfPossible();
  });

  $('#sprintSelection').change(function() {
    updateChartIfPossible();
  });

  $('#burnupBudget').change(function() {
    var sprintId = getSelectedSprintId();
    if(sprintId != undefined)
    {
      localStorage.setItem('budget_sprint_' + sprintId, getBurnupBudgetField());
      updateChartIfPossible();
    }
    else
    {
      setBurnupBudgetField('');
    }
  });

  $('#availability').change(function() {
    var sprintId = getSelectedSprintId();
    if(sprintId != undefined)
    {
      localStorage.setItem('availability_sprint_' + sprintId, getAvailabilityField());
      updateChartIfPossible();
    }
    else
    {
      setAvailabilityField('');
    }
  });

  $(window).resize(function() {
    updateChartIfPossible();
  });

  main();

});


