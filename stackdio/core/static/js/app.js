var stackdio = {};

requirejs.config({
   paths: {
        'jquery': 'lib/jquery',
        'bootstrap': 'lib/bootstrap',
        'sammy': 'lib/sammy',
        'knockout': 'lib/knockout',
        'underscore': 'lib/underscore',
        'datatables': 'lib/jquery.dataTables.min',
        'jquery-ui': 'lib/jquery-ui-min',
    }, 

    // Use shim for plugins that does not support AMD
    shim: {
        'bootstrap': ['jquery'],
        'knockout': ['jquery'],
        'sammy': ['jquery'],
        'datatables': ['jquery'],
        'jquery-ui': ['jquery']
    },

});

require(["bootstrap"], function () { });
require(["underscore"], function () { });
require(["app/stackdio"], function () { });
