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

define([
    'jquery',
    'knockout',
    'bootbox',
    'utils/utils',
    'models/stack',
    'fuelux'
], function ($, ko, bootbox, utils, Stack) {
    'use strict';

    return function () {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: false,
                title: window.stackdio.stackTitle,
                href: '/stacks/' + window.stackdio.stackId + '/'
            },
            {
                active: true,
                title: 'Logs'
            }
        ];

        self.selectedLogUrl = null;
        self.log = ko.observable();

        self.stack = ko.observable();
        self.reset = function () {
            self.stack(new Stack(window.stackdio.stackId, self));
            self.selectedLogUrl = null;
            self.log('Select a log...');
        };

        self.reload = function (initial) {
            if (typeof initial === 'undefined') {
                initial = false;
            }
            if (self.selectedLogUrl) {
                if (initial) {
                    self.log('Loading...');
                }
                $.ajax({
                    method: 'GET',
                    url: self.selectedLogUrl,
                    headers: {
                        'Accept': 'text/plain'
                    }
                }).done(function (log) {
                    var logDiv = document.getElementById('log-text');
                    var pos = logDiv.scrollTop;
                    var height = logDiv.scrollHeight;
                    self.log(log);
                    if (height - pos < 550 || initial) {
                        logDiv.scrollTop = logDiv.scrollHeight - 498;
                    }
                }).fail(function (jqxhr) {
                    if (jqxhr.status == 403) {
                        window.location.reload(true);
                    } else {
                        utils.growlAlert('Failed to load log', 'danger');
                    }
                });
            }
        };

        self.dataSource = function (parentData, callback) {
            var ret;
            if (parentData.text === 'Latest') {
                ret = self.stack().latestLogs();
            } else if (parentData.text === 'Historical') {
                ret = self.stack().historicalLogs();
            } else {
                // This is the root level
                self.stack().loadLogs();
                ret = [
                    {text: 'Latest', type: 'folder'},
                    {text: 'Historical', type: 'folder'}
                ];
            }

            callback({
                data: ret
            })
        };

        self.reset();

        var $el = $('#log-selector');

        $el.tree({
            dataSource: self.dataSource,
            cacheItems: false,
            folderSelect: false
        });

        self.intervalId = null;

        $el.on('selected.fu.tree', function (event, data) {
            self.selectedLogUrl = data.target.url;
            clearInterval(self.intervalId);
            self.reload(true);
            if (data.target.url.indexOf('latest') >= 0) {
                self.intervalId = setInterval(self.reload, 3000);
            }
        });


    };
});
