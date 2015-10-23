
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
    'utils/utils'
], function ($, ko, bootbox, utils) {
    'use strict';

    // Define the command model.
    function Group(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                name: raw,
                url: '/api/groups/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Editable fields
        this.name = ko.observable();

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Group.constructor = Group;

    Group.prototype._process = function (raw) {
        this.name(raw.name);
    };

    // Reload the current group
    Group.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (group) {
            self.raw = group;
            self._process(group);
        });
    };

    Group.prototype.save = function () {
        var self = this;
        $.ajax({
            method: 'PUT',
            url: this.raw.url,
            data: JSON.stringify({
                name: self.name()
            })
        }).done(function (group) {
            utils.growlAlert('Successfully saved group!', 'success');
        }).fail(function (jqxhr) {
            var message = '';
            try {
                var resp = JSON.parse(jqxhr.responseText);

                for (var key in resp) {
                    if (resp.hasOwnProperty(key)) {
                        if (keys.indexOf(key) >= 0) {
                            var el = $('#' + key);
                            el.addClass('has-error');
                            resp[key].forEach(function (errMsg) {
                                el.append('<span class="help-block">' + errMsg + '</span>');
                            });
                        } else if (key === 'non_field_errors') {
                            resp[key].forEach(function (errMsg) {
                                if (errMsg.indexOf('name') >= 0) {
                                    var el = $('#name');
                                    el.addClass('has-error');
                                    el.append('<span class="help-block">A group with this name already exists.</span>');
                                }
                            });
                        } else {
                            var betterKey = key.replace('_', ' ');

                            resp[key].forEach(function (errMsg) {
                                message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                            });
                        }
                    }
                }
                if (message) {
                    message = '<dl class="dl-horizontal">' + message + '</dl>';
                }
            } catch (e) {
                message = 'Oops... there was a server error.  This has been reported to ' +
                    'your administrators.'
            }
            if (message) {
                bootbox.alert({
                    title: 'Error saving group',
                    message: message
                });
            }
        });
    };

    Group.prototype.delete = function () {
        $.ajax({
            method: 'DELETE',
            url: this.raw.url
        })
    };

    return Group;
});