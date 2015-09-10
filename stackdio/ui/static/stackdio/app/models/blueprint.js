
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
    'models/host-definition'
], function ($, ko, bootbox, HostDefinition) {
    'use strict';

    // Define the stack model.
    function Blueprint(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/stacks/' + raw + '/hosts/'
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
        this.createUsers = ko.observable();

        // Lazy-loaded properties (not returned from the main blueprint endpoint)
        this.properties = ko.observable({});
        this.hostDefinitions = ko.observableArray([]);
        this.formulaVersions = ko.observableArray([]);

        if (needReload) {
            this.reload();
        } else {
            this._process(raw);
        }
    }

    Blueprint.constructor = Blueprint;

    Blueprint.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.createUsers(raw.create_users);
    };

    // Reload the current stack
    Blueprint.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (blueprint) {
            self.raw = blueprint;
            self._process(blueprint);
        });
    };

    // Lazy-load the properties
    Blueprint.prototype.loadProperties = function () {
        var self = this;
        $.ajax({
            method: 'GET',
            url: this.raw.properties
        }).done(function (properties) {
            self.properties(properties);
        });
    };

    Blueprint.prototype.loadHostDefinitions = function () {
        var self = this;

        var tmpHostDefs = [];

        // Probably not the best way to do this, but I don't anticipate a blueprint having more
        // than 50 host definitions.  Just putting this in here in case it does happen so
        // that the UI doesn't break.
        function doLoad(url) {
            $.ajax({
                method: 'GET',
                url: url
            }).done(function (hostDefinitions) {
                tmpHostDefs.push.apply(tmpHostDefs, hostDefinitions.results.map(function (rawDef) {
                    return new HostDefinition(rawDef, self.parent);
                }));
                if (hostDefinitions.next === null) {
                    self.hostDefinitions(tmpHostDefs);
                } else {
                    doLoad(hostDefinitions.next);
                }
            });
        }

        doLoad(this.raw.host_definitions);
    };

    Blueprint.prototype.delete = function () {
        var self = this;
        var blueprintTitle = this.title();
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + blueprintTitle + '</strong>',
            message: 'Are you sure you want to delete <strong>' + blueprintTitle + '</strong>?',
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
                    }).done(function (blueprint) {
                        // Nothing to do here?
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
                            title: 'Error deleting blueprint',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Blueprint;
});