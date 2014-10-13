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

requirejs.config({
   paths: {
        'jquery': 'bower_components/jquery/jquery.min',
        'bootstrap': 'bower_components/bootstrap/dist/js/bootstrap.min',
        'bootstrap-select': 'bower_components/bootstrap-select/bootstrap-select.min',
        'bootstrap-typeahead': 'bower_components/typeahead.js/dist/typeahead.min',
        'bootbox': 'bower_components/bootbox/bootbox',
        'ladda': 'bower_components/ladda/js/ladda',
        'knockout': 'bower_components/knockout.js/knockout',
        'q': 'bower_components/q/q.min',
        'underscore': 'bower_components/underscore/underscore',
        'postal': 'bower_components/postal.js/lib/postal.min',
        'moment': 'bower_components/moment/min/moment.min',
        'spin': 'bower_components/spin.js/spin'
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
function (select, typeahead, _, RootAPI, navigation) {

    // Set up a template compiler for underscore
    _.compile = function (templ) {
        var compiled = this.template(templ);
        compiled.render = function(ctx) {
            return this(ctx);
        }
        return compiled;
    };

    // Load the root API object and then render the navigation view which, in turn, requires
    // the default view of 'welcome'
    RootAPI.load().then(function (apiNamespaces) {
        require(['viewmodel/navigation'], function (nav) { });
    }).catch(function (error) {
        console.error(error.name, error.message);
    });
});
