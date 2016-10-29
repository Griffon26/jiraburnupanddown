# jira-burn-up-and-down
A burndown chart for Jira that also keeps track of hours spent on a separate fixed-size budget

Jira burn-up-and-down is an [electron](http://electron.atom.io/) app that talks to the 
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

# Installation instructions
TBD