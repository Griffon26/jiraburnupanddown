#!/usr/bin/env python

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import re
import urllib.parse as urlparse

port = 8080
jiraversion = 6

class JiraRequestHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        o = urlparse.urlparse(self.path)
        query_components = urlparse.parse_qs(o.query)


        resources = [
            (r'rest/greenhopper/1.0/xboard/selectorData', {}, 'getScrumBoards.json'),
            (r'rest/greenhopper/1.0/sprintquery/[0-9]+', {}, 'getSprints.json'),
            (r'rest/greenhopper/1.0/rapid/charts/sprintreport', {}, 'getSprintDates.json'),
            (r'rest/api/2/search', { 'jql' : r'issuetype = Sub-task .*' }, 'getIssues.json'),
            (r'rest/api/2/search', { 'jql' : r'issuekey in .*' }, 'getEffortForIssues.json'),
            (r'rest/greenhopper/1.0/rapid/charts/scopechangeburndownchart', {}, 'getScopeChangeBurndownChart.json'),
            (r'rest/api/2/search', { 'jql' : r'.*(issuetype = Support).*' }, 'getIssueWorklogs.json')
        ]

        for resource, query, datafile in resources:
            if re.match(resource, o.path[1:]) and \
               all([(key in query_components and re.match(value, query_components[key][0]))
                    for key, value in query.items()]):
                with open('jira%d/%s' % (jiraversion, datafile), 'rt') as f:
                    data = f.read().encode("utf-8")

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Content-length', len(data))
                    self.end_headers()
                    self.wfile.write(data)
                    return

        self.send_error(404, 'Data was requested for an unknown resource: %s' % self.path)

httpd = TCPServer(("", port), JiraRequestHandler)

print('Fake JIRA server running on port', port)
httpd.serve_forever()

