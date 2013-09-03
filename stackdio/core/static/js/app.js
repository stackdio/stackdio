var stackdio = {};

requirejs.config({
   paths: {
        'jquery': 'lib/jquery',
        'bootstrap': 'lib/bootstrap',
        'bootstrap-select': 'lib/bootstrap-select.min',
        'knockout': 'lib/knockout',
        'underscore': 'lib/underscore',
        'datatables': 'lib/jquery.dataTables.min',
        'jquery-ui': 'lib/jquery-ui-min',
    }, 

    shim: {
        'bootstrap': ['jquery'],
        'bootstrap-select': ['bootstrap'],
        'datatables': ['jquery'],
        'jquery-ui': ['jquery']
    },

});

require(["bootstrap-select", "datatables", "jquery-ui", "underscore", "app/viewmodel/stackdio"], function () { });
