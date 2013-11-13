var stackdio = {};

requirejs.config({
   paths: {
        'jquery': 'components/jquery/jquery.min',
        'jui': 'components/jquery-ui-amd/jquery-ui-1.10.0/jqueryui',
        'bootstrap': 'components/bootstrap/dist/js/bootstrap.min',
        'bootstrap-select': 'components/bootstrap-select/bootstrap-select.min',
        'bootstrap-typeahead': 'components/typeahead.js/dist/typeahead.min',
        'knockout': 'components/knockoutjs/build/output/knockout-latest',
        'q': 'components/q/q.min',
        'underscore': 'components/underscore-amd/underscore-min',
        'moment': 'components/moment/min/moment.min'
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
    'viewmodel/stackdio'
], 
function () {

});
