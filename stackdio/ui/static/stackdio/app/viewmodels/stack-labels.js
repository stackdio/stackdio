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

define([
    'jquery',
    'knockout',
    'bootbox',
    'utils/utils',
    'generics/pagination',
    'models/stack',
    'models/label'
], function ($, ko, bootbox, utils, Pagination, Stack, Label) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: false,
                title: 'Stack Detail',
                href: '/stacks/' + window.stackdio.stackId + '/'
            },
            {
                active: true,
                title: 'Stack Labels'
            }
        ],
        stack: ko.observable(),
        autoRefresh: false,
        model: Label,
        baseUrl: '/stacks/',
        initialUrl: '/api/stacks/' + window.stackdio.stackId + '/labels/',
        sortableFields: [
            {name: 'key', displayName: 'Key', width: '50%'},
            {name: 'value', displayName: 'Value', width: '50%'}
        ],
        init: function () {
            this._super();
            this.stack(new Stack(window.stackdio.stackId, this));
        },
        saveLabels: function () {
            var ajaxCalls = [];
            var self = this;
            this.objects().forEach(function (label) {
                ajaxCalls.push($.ajax({
                    method: 'PUT',
                    url: self.stack().raw.labels + label.key() + '/',
                    data: JSON.stringify({
                        value: label.value()
                    })
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving label',
                        'Errors saving label for ' + label.key() + ':<br>');
                }));
            });

            $.when.apply(this, ajaxCalls).done(function () {
                utils.growlAlert('Successfully saved labels!', 'success');
            });

        }
    });
});
