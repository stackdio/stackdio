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

var bower_path = '../lib/bower_components/';

requirejs.config({
    baseUrl: '/static/stackdio/app',

    paths: {
        'jquery': bower_path + 'jquery/jquery.min',
        'bootstrap': bower_path + 'bootstrap/dist/js/bootstrap.min',
        'bootstrap-select': bower_path + 'bootstrap-select/bootstrap-select.min',
        'bootstrap-typeahead': bower_path + 'typeahead.js/dist/typeahead.min',
        'bootbox': bower_path + 'bootbox/bootbox',
        'ladda': bower_path + 'ladda/js/ladda',
        'knockout': bower_path + 'knockout.js/knockout',
        'q': bower_path + 'q/q',
        'underscore': bower_path + 'underscore/underscore',
        'postal': bower_path + 'postal.js/lib/postal.min',
        'moment': bower_path + 'moment/min/moment.min',
        'spin': bower_path + 'spin.js/spin'
    },

    shim: {
        'bootstrap': ['jquery'],
        'bootstrap-select': ['bootstrap'],
        'bootbox': ['bootstrap'],
        'bootstrap-typeahead': ['bootstrap'],
        'ladda': ['spin']
    }
});

require([
    'bootstrap-select',
    'bootstrap-typeahead',
    'underscore',
    'api/Root'
],
function (select, typeahead, _, RootAPI) {

    // Set up a template compiler for underscore
    _.compile = function (templ) {
        var compiled = this.template(templ);
        compiled.render = function (ctx) {
            return this(ctx);
        };
        return compiled;
    };

    // Load the root API object and then render the navigation view which, in turn, requires
    // the default view of 'welcome'
    RootAPI.load().then(function (apiNamespaces) {
        require(['viewmodel/navigation'], function (nav) {
        });
    }).catch(function (error) {
        console.error(error.name, error.message);
    });
});
