
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
    'models/host-definition'
], function ($, ko, bootbox, utils, HostDefinition) {
    'use strict';

    // Define the snapshot model.
    function Snapshot(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/cloud/snapshots/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Save the id
        this.id = raw.id;

        // Editable fields
        this.title = ko.observable();
        this.description = ko.observable();
        this.accountId = ko.observable();
        this.snapshotId = ko.observable();
        this.filesystemType = ko.observable();

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Snapshot.constructor = Snapshot;

    Snapshot.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.accountId(raw.account);
        this.snapshotId(raw.snapshot_id);
        this.filesystemType(raw.filesystem_type);
    };

    // Reload the current snapshot
    Snapshot.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (snapshot) {
            self.raw = snapshot;
            self._process(snapshot);
        });
    };

    Snapshot.prototype.save = function () {
        var self = this;
        var keys = ['title', 'description', 'snapshot_id', 'filesystem_type'];

        keys.forEach(function (key) {
            var el = $('#' + key);
            el.removeClass('has-error');
            var help = el.find('.help-block');
            help.remove();
        });

        $.ajax({
            method: 'PUT',
            url: self.raw.url,
            data: JSON.stringify({
                title: self.title(),
                description: self.description(),
                snapshot_id: self.snapshotId(),
                filesystem_type: self.filesystemType()
            })
        }).done(function (snapshot) {
            utils.growlAlert('Successfully saved snapshot!', 'success');
            try {
                self.parent.snapshotTitle(snapshot.title);
            } catch (e) {}
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'snapshot', keys);
        });
    };

    Snapshot.prototype.delete = function () {
        var self = this;
        var snapshotTitle = this.title();
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + snapshotTitle + '</strong>',
            message: 'Are you sure you want to delete <strong>' + snapshotTitle + '</strong>?',
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
                        if (window.location.pathname !== '/snapshots/') {
                            window.location = '/snapshots/';
                        } else if (self.parent && typeof self.parent.reload === 'function') {
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
                            title: 'Error deleting snapshot',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Snapshot;
});