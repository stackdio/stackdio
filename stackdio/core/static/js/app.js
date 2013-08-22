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

require(["sammy"], function() { });
require(["underscore"], function() { });
require(["bootstrap"], function() { });
require(["datatables"], function() { });
require(["jquery-ui"], function() { });
require(["app/stackdio"], function () { });


        
// Start the main app logic.
requirejs(['jquery'],
    function   () {
        var getCookie = function (name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = $.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        stackdio.csrftoken = getCookie('csrftoken');
});
