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
        newLabels: ko.observableArray([]),
        newLabelKey: ko.observable(),
        autoRefresh: false,
        model: Label,
        baseUrl: '/stacks/',
        initialUrl: '/api/stacks/' + window.stackdio.stackId + '/labels/',
        sortableFields: [
            {name: 'key', displayName: 'Key', width: '45%'},
            {name: 'value', displayName: 'Value', width: '45%'}
        ],
        init: function () {
            this._super();
            this.newLabelKey(null);
            this.stack(new Stack(window.stackdio.stackId, this));
        },
        addNewLabel: function () {
            var $el = $('#new-label-form');

            $el.removeClass('has-error');

            var self = this;
            var dup = false;
            this.sortedObjects().forEach(function (label) {
                if (label.key() === self.newLabelKey()) {
                    dup = true;
                }
            });

            this.newLabels().forEach(function (label) {
                if (label.key === self.newLabelKey()) {
                    dup = true;
                }
            });

            if (dup) {
                utils.growlAlert('You may not have two labels with the same key.', 'danger');
                $el.addClass('has-error');
                return;
            }

            this.newLabels.push({
                key: this.newLabelKey(),
                value: ko.observable(null)
            });
            this.newLabelKey(null);
        },
        deleteNewLabel: function (label) {
            this.newLabels.remove(label);
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

            this.newLabels().forEach(function (label) {
                ajaxCalls.push($.ajax({
                    method: 'POST',
                    url: self.stack().raw.labels,
                    data: JSON.stringify({
                        key: label.key,
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
