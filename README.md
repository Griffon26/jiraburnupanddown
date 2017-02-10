# Jira burn-up-and-down
A Scrum burndown chart for Jira that also keeps track of hours spent on a separate fixed-size budget

Jira burn-up-and-down is a python application that talks to the 
[Jira](https://www.atlassian.com/software/jira) REST API to display a Scrum burndown chart
combined with a burnup chart that shows how much of a fixed-size budget has been spent.

Combining these two charts will help you realize how much additional points of sprint work
should be completed when not all of the fixed-size budget has been used up, in order to keep
sprint velocity constant.

Another difference with the built-in Jira burndown chart is that this one does not mix sprint
progress with sprint scope changes. Sprint progress is plotted as usual, while sprint scope
changes are shown as a change in the baseline of the chart. 

All in all this chart gives a much clearer view of what is expected of the team in order to
maintain their velocity.

## Screenshot

![A screenshot of JIRA burn-up-and-down](/docs/images/screenshot.png?raw=true)

## Installation instructions

    python3 -m pip install jiraburnupanddown

*Note: when using the above command make sure you are running a python version
for which [PyQt5 wheels](https://pypi.python.org/pypi/PyQt5) are available.*

## Usage instructions

This section describes two things to keep in mind when you plan to use this application.

### Distribute a story's points over its sub-tasks

I believe that sprint progress must be measured in points, not in estimated remaining time.
I also think that it's valuable to see progress when tasks are completed instead of only
when user stories are completed.

For this reason I distribute the points of a story over the sub-tasks and, lacking a points
field for sub-tasks in Jira, fill in the number of points in the original estimate field.
Jira may see that field as hours, but I consider it to be points.

This application follows the same approach and tracks the completion of sub-tasks in Jira.
It uses the original estimate field as the size (in points) of a sub-task.

### No overlap between burnup and burndown

The point of this application is to show you if there is going to be a conflict between
finishing sprint content and spending time on a separate activity counted in hours.

This only works if the query for burnup tasks (specified in the connection dialog) does
not return any of the sub-tasks that are part of the sprint.

## Dependencies

* numpy
* PyQt5
* pyqtgraph
* python-dateutil
* pytz
* requests
* tzlocal

