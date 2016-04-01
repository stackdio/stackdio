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
    'utils/utils',
    'generics/pagination',
    'models/label'
], function ($, ko, utils, Pagination, Label) {
    'use strict';

    return Pagination.extend({
        parentModel: null,
        parentId: null,
        parentObject: ko.observable(),
        newLabels: ko.observableArray([]),
        newLabelKey: ko.observable(),
        autoRefresh: false,
        model: Label,
        sortableFields: [
            {name: 'key', displayName: 'Key', width: '45%'},
            {name: 'value', displayName: 'Value', width: '45%'}
        ],
        init: function () {
            this._super();
            this.newLabelKey(null);
            this.parentObject(new this.parentModel(this.parentId, this));
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
                var value = label.value();

                ajaxCalls.push($.ajax({
                    method: 'PUT',
                    url: self.parentObject().raw.labels + label.key() + '/',
                    data: JSON.stringify({
                        value: value ? value : null
                    })
                }).fail(function (jqxhr) {
                    if (jqxhr.status !== 404) {
                        utils.alertError(jqxhr, 'Error saving label',
                            'Errors saving label for ' + label.key() + ':<br>');
                    }
                }));
            });

            this.newLabels().forEach(function (label) {
                var value = label.value();

                ajaxCalls.push($.ajax({
                    method: 'POST',
                    url: self.parentObject().raw.labels,
                    data: JSON.stringify({
                        key: label.key,
                        value: value ? value : null
                    })
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving label',
                        'Errors saving label for ' + label.key + ':<br>');
                }));
            });

            $.when.apply(this, ajaxCalls).done(function () {
                utils.growlAlert('Successfully saved labels!', 'success');
                self.newLabels([]);
                self.reload();
            });

        }
    });
});
