
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
    'bootbox'
], function ($, ko, bootbox) {
    'use strict';

    // Define the security group model.
    function SecurityGroup(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/commands/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Save the id
        this.id = raw.id;

        // Editable fields
        this.name = ko.observable();
        this.description = ko.observable();
        this.groupId = ko.observable();
        this.default = ko.observable();
        this.managed = ko.observable();

        if (needReload) {
            this.reload();
        } else {
            this._process(raw);
        }
    }

    SecurityGroup.constructor = SecurityGroup;

    SecurityGroup.prototype._process = function (raw) {
        this.name(raw.name);
        this.description(raw.description);
        this.groupId(raw.group_id);
        this.default(raw.default);
        this.managed(raw.managed);
    };

    // Reload the current security group
    SecurityGroup.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (group) {
            self.raw = group;
            self._process(group);
        });
    };

    SecurityGroup.prototype.delete = function () {
        var self = this;
        var securityGroupName = this.name();

        var message = 'Are you sure you want to delete <strong>' + securityGroupName + '</strong>?';

        if (this.managed()) {
            message += '<br>This <strong>will</strong> delete the group from the provider in ' +
                'addition to locally.';
        } else {
            message += '<br>This will <strong>not</strong> delete the group on the provider, it ' +
                'will only delete stackd.io\'s record of it.';
        }

        bootbox.confirm({
            title: 'Confirm delete of <strong>' + securityGroupName + '</strong>',
            message: message,
            buttons: {
                confirm: {
                    label: 'Delete',
                    className: 'btn-danger'
                }
            },
            callback: function (result) {
                if (result) {
                    $.ajax({
                        method: 'DELETE',
                        url: self.raw.url
                    }).done(function () {
                        if (self.parent.reload) {
                            self.parent.reload();
                        }
                    }).fail(function (jqxhr) {
                        var message;
                        try {
                            var resp = JSON.parse(jqxhr.responseText);
                            message = resp.detail.join('<br>');
                        } catch (e) {
                            message = 'Oops... there was a server error.  This has been reported ' +
                                'to your administrators.';
                        }
                        bootbox.alert({
                            title: 'Error deleting security group',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return SecurityGroup;
});