/*!
  * Copyright 2014,  Digital Reasoning
  *
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  *
  *     http://www.apache.org/licenses/LICENSE-2.0
  *
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  *
*/

{% load staticfiles %}

{# Templatize this file so that the static files always work even if the static url changes #}

{# Grab the bower path #}
{# This is better to be templatized.  This way our optimization process works easier #}
{% with '../lib/bower_components' as bower_path %}

requirejs.config({
    baseUrl: '{% static 'stackdio/app' %}',
    paths: {
        'bloodhound': '{{ bower_path }}/typeahead.js/dist/bloodhound',
        'bootbox': '{{ bower_path }}/bootbox.js/bootbox',
        'bootstrap': '{{ bower_path }}/bootstrap/dist/js/bootstrap',
        'domReady': '{{ bower_path }}/requirejs-domReady/domReady',
        'jquery': '{{ bower_path }}/jquery/jquery',
        'knockout': '{{ bower_path }}/knockout/dist/knockout',
        'ladda': '{{ bower_path }}/ladda/dist/ladda',
        'moment': '{{ bower_path }}/moment/moment',
        'spin': '{{ bower_path }}/ladda/dist/spin',
        'typeahead': '{{ bower_path }}/typeahead.js/dist/typeahead.jquery',
        'underscore': '{{ bower_path }}/underscore/underscore'
    },
    shim: {
        bootstrap: {
            deps: ['jquery']
        },
        typeahead: {
            deps: ['jquery'],
            init: function($) {
                // This fixes an issue with typeahead.  Once this typeahead bug is fixed in a
                // future release, this whole typeahead entry in the shim can be removed, but this
                // is robust enough to work with OR without the bugfix.
                var registry = require.s.contexts._.registry;
                if (registry.hasOwnProperty('typeahead.js')) {
                    return registry['typeahead.js'].factory($);
                } else if (registry.hasOwnProperty('typeahead')) {
                    return registry['typeahead'].factory($);
                } else {
                    console.error('Unable to load typeahead.js.');
                }
            }
        }
    }
});
{% endwith %}

// Add our custom capitalize method
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};

require([
    'jquery',
    'bootstrap',
    'knockout',
    'utils/mobile-fix',
    '{{ viewmodel }}',
    'domReady!'
], function($, bootstrap, ko, mf, vm) {
    // Function for getting cookies
    // pulled from Django 1.8 documentation
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

    // Check for safe methods
    // pulled from Django 1.8 documentation
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Grab the CSRF token
    var csrftoken = getCookie('csrftoken');

    // Set up some basic jQuery ajax settings globally so we don't have to worry about it later
    $.ajaxSetup({
        contentType: 'application/json',
        headers: {
            'Accept': 'application/json'
        },
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.method) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Make the search bar resize magically!
    $(document).on("focus", '[data-action="grow"]', function() {
        var width = $(window).width();
        if (width > 767) {
            var newWidth = width > 991 ? 350 : 250;
            $(this).animate({
                width: newWidth
            });
        }
    });

    $(document).on("blur", '[data-action="grow"]', function() {
        if ($(window).width() > 767) {
            $(this).animate({
                width: 180
            })
        }
    });

    // Apply the bindings for our viewmodel
    ko.applyBindings(new vm());
});
