var app = require('app');  // Module to control application life.
var BrowserWindow = require('browser-window');  // Module to create native browser window.

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
var mainWindow = null;

app.commandLine.appendSwitch('ignore-certificate-errors');

// Quit when all windows are closed.
app.on('window-all-closed', function() {
  // On OS X it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform != 'darwin') {
    app.quit();
  }
});

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.on('ready', function() {
  // Create the browser window.
  mainWindow = new BrowserWindow({width: 900, height: 650});
  //mainWindow.setMenu(null);

  // and load the index.html of the app.
  mainWindow.loadUrl('file://' + __dirname + '/login.html');

  // Open the DevTools.
  //mainWindow.webContents.openDevTools();

  // Emitted when the window is closed.
  mainWindow.on('closed', function() {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null;
  });
});

var ipc = require('ipc');
var credentials = {};


var settings = { 'logging' : false,
                 'write'   : false,
                 'read'    : true }

ipc.on('set_credentials', function(event, arg) {
  credentials = arg;
  event.returnValue = 'ok';
});

ipc.on('get_credentials', function(event) {
  event.returnValue = credentials;
});

ipc.on('get_settings', function(event) {
  event.returnValue = settings;
});


