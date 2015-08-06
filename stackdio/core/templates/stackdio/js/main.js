{% load staticfiles %}

var bowerPath = '../lib/bower_components/';

requirejs.config({
    baseUrl: '{% static 'stackdio/app' %}',
    paths: {
        'bootstrap': bowerPath + 'bootstrap/dist/js/bootstrap.min',
        'jquery': bowerPath + 'jquery/jquery.min',
        'knockout': bowerPath + 'knockout/dist/knockout',
        'knockout-mapping': bowerPath + 'knockout-mapping/knockout.mapping',
        'moment': bowerPath + 'moment/moment',
        'underscore': bowerPath + 'underscore/underscore-min'
    },
    shim: {
        bootstrap: {
            deps: ['jquery']
        },
        underscore: {
            exports: '_'
        }
    }
});



require([
    'jquery',
    'bootstrap',
    'knockout',
    'utils/mobile-fix',
    '{{ viewmodel }}'
], function($, bootstrap, ko, mf, vm) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Grab the CSRF token
    var csrftoken = getCookie('csrftoken');

    // Just set by default so we never have to worry about it!
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Make sure our app works in view mode
    if(("standalone" in window.navigator) && window.navigator.standalone) {
        var sel = 'a';
        $("body").delegate(sel, "click", function(e) {
            if($(this).attr("target") == undefined || $(this).attr("target") == "" || $(this).attr("target") == "_self") {
                var d = $(this).attr("href");
                if(!d.match(/^http(s?)/g)) { e.preventDefault(); self.location = d; }
            }
        });
    }

    // Apply the bindings for our VM
    ko.applyBindings(vm);
});