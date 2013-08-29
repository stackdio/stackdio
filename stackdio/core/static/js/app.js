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

    // Use shim for plugins that does not support AMD
    shim: {
        'bootstrap': ['jquery'],
        'bootstrap-select': ['bootstrap'],
        'knockout': ['jquery'],
        'datatables': ['jquery'],
        'jquery-ui': ['jquery']
    },

});

require(["bootstrap", "bootstrap-select"], function () {
    $('.selectpicker').selectpicker();
});
require(["underscore"], function () { });
require(["app/stackdio"], function () { });
