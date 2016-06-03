/*!
  * Copyright 2016,  Digital Reasoning
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

{% with '../lib/bower_components' as bower_path %}

requirejs.config({
    baseUrl: '{% static 'stackdio/app' %}',
    paths: {
        'bloodhound': '{{ bower_path }}/typeahead.js/dist/bloodhound',
        'bootbox': '{{ bower_path }}/bootbox.js/bootbox',
        'bootstrap': '{{ bower_path }}/bootstrap/dist/js/bootstrap',
        'cookie': '{{ bower_path }}/js-cookie/src/js.cookie',
        'domReady': '{{ bower_path }}/requirejs-domReady/domReady',
        'fuelux': '{{ bower_path }}/fuelux/dist/js/fuelux',
        'jquery': '{{ bower_path }}/jquery/dist/jquery',
        'knockout': '{{ bower_path }}/knockout/dist/knockout',
        'ladda': '{{ bower_path }}/ladda/js/ladda',
        'moment': '{{ bower_path }}/moment/moment',
        'select2': '{{ bower_path }}/select2/dist/js/select2',
        'spin': '{{ bower_path }}/ladda/js/spin',
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
    'cookie',
    'bootstrap',
    'fuelux',
    'utils/mobile-fix',
    'domReady!'
], function($, Cookie) {
    // Check for safe methods
    // pulled from Django 1.8 documentation
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Grab the CSRF token
    var csrftoken = Cookie.get('csrftoken');

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

    var advancedWarning = Cookie.get('displayAdvancedWarning');

    if (!window.stackdio.advancedView && typeof advancedWarning === 'undefined') {
        // Save the element
        var $el = $('.stackdio-advanced-warning');

        // Show the message
        $el.removeClass('stackdio-advanced-warning');

        function turnOfWarning(e) {
            Cookie.set('displayAdvancedWarning', false, {expires: 365, path: '/'});
        }

        // Register our click handlers to set the cookie
        $('#advanced-warning-dismiss').click(turnOfWarning);
        $('#advanced-warning-button').click(turnOfWarning)
    }
});
