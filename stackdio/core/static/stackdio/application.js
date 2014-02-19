var stackdio = {};

requirejs.config({
   paths: {
        'jquery': 'bower_components/jquery/jquery.min',
        'jui': 'bower_components/jquery-ui-amd/jquery-ui-1.10.0/jqueryui',
        'bootstrap': 'bower_components/bootstrap/dist/js/bootstrap.min',
        'bootstrap-select': 'bower_components/bootstrap-select/bootstrap-select.min',
        'bootstrap-typeahead': 'bower_components/typeahead.js/dist/typeahead.min',
        'knockout': 'bower_components/knockout.js/knockout',
        'q': 'bower_components/q/q.min',
        'underscore': 'bower_components/underscore-amd/underscore-min',
        'postal': 'bower_components/postal.js/lib/postal.min',
        'moment': 'bower_components/moment/min/moment.min'
    },

    shim: {
        'bootstrap': ['jquery'],
        'bootstrap-select': ['bootstrap'],
        'bootstrap-typeahead': ['bootstrap']
    }
});

require([
    'bootstrap-select',
    'bootstrap-typeahead',
    'underscore',
    'api/Root'
], 
function (select, typeahead, _, RootAPI, navigation) {
    RootAPI.load().then(function (apiNamespaces) {
        require(['viewmodel/navigation'], function (nav) {

        });
    }).catch(function (error) {
        console.error(error.name, error.message);
    });
});
