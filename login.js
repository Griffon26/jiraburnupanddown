
window.$ = window.jQuery = require('jquery');
var ipc = require('ipc');

$(function() {

  var creds = ipc.sendSync('get_credentials');
  var settings = ipc.sendSync('get_settings');

  if(settings.read)
  {
    window.location.href = 'burndown.html';
  }
  else
  {
    $('#jiraurl').keyup(function (e) { if (e.keyCode == 13) { $('#username').focus(); } });
    $('#username').keyup(function (e) { if (e.keyCode == 13) { $('#password').focus(); } });
    $('#password').keyup(function (e) { if (e.keyCode == 13) { $('#login').click(); } });

    /* By default use the data we have stored from the last time */
    $('#jiraurl').val(localStorage.getItem('jiraurl'));
    $('#username').val(creds.username);
    $('#password').val(creds.password);

    $("#login").click( function()
    {
      var jiraurl = $("#jiraurl").val();
      var username = $("#username").val();
      var password = $("#password").val();

      try {

      $.ajax({
        async: false,
        type: 'GET',
        url: jiraurl + '/rest/auth/1/session/',
        headers: { 'Authorization' : 'Basic ' + btoa(username + ':' + password) },
        success: function(jsonData) {

          localStorage.setItem('jiraurl', jiraurl);

          ipc.sendSync('set_credentials', { 'username' : username,
                                            'password' : password });

          window.location.href = 'burndown.html';
        },
        error: function(req, textStatus, errorThrown) {
          if(errorThrown == 'Forbidden')
          {
            errorThrown += ' (this probably means you\'ll have to login with a browser and solve a captcha :-/ )';
          }
          $(".loginstatus").text(errorThrown);
        }
      });

      }
      catch(err) {
        console.log("Something went wrong");
      }
    });
  }
});

