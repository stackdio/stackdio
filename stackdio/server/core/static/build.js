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

({
    baseUrl: "./js",
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
    name: "app",
    out: "stackdio-built.js"
})