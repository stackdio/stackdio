var stackdio = {};

requirejs.config({
   paths: {
        'jquery': 'lib/jquery',
        'bootstrap': 'lib/bootstrap.min',
        'bootstrap-select': 'lib/bootstrap-select.min',
        'bootstrap-typeahead': 'lib/bootstrap-typeahead.min',
        'knockout': 'lib/knockout',
        'underscore': 'lib/underscore',
        'jquery-ui': 'lib/jquery-ui-1.10.3.custom.min',
        'moment': 'lib/moment'
    }, 

    shim: {
        'bootstrap': ['jquery'],
        'bootstrap-select': ['bootstrap'],
        'bootstrap-typeahead': ['bootstrap'],
        'jquery-ui': ['jquery']
    },

});

require(["bootstrap-select", "bootstrap-typeahead", "jquery-ui", "underscore", "app/viewmodel/stackdio"], function () { });
