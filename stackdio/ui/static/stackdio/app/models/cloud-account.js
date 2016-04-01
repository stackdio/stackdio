
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
    'utils/utils'
], function ($, ko, bootbox, utils) {
    'use strict';

    // Define the cloud account model.
    function CloudAccount(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/cloud/accounts/' + raw + '/'
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
        this.slug = ko.observable();
        this.region = ko.observable();
        this.provider = ko.observable();
        this.vpcId = ko.observable();
        this.createSecurityGroups = ko.observable();

        // Lazy-loaded properties (not returned from the main cloud account endpoint)
        this.properties = ko.observable({});
        this.hostDefinitions = ko.observableArray([]);
        this.formulaVersions = ko.observableArray([]);

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    CloudAccount.constructor = CloudAccount;

    CloudAccount.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.slug(raw.slug);
        this.region(raw.region);
        this.provider(raw.provider);
        this.vpcId(raw.vpc_id);
        this.createSecurityGroups(raw.create_security_groups);
    };

    // Reload the current cloud account
    CloudAccount.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (account) {
            self.raw = account;
            self._process(account);
        });
    };

    // Lazy-load the properties
    CloudAccount.prototype.loadProperties = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('properties')) {
            this.raw.properties = this.raw.url + 'properties/';
        }
        return $.ajax({
            method: 'GET',
            url: this.raw.properties
        }).done(function (properties) {
            self.properties(properties);
        });
    };

    CloudAccount.prototype.saveProperties = function () {
        $.ajax({
            method: 'PUT',
            url: this.raw.properties,
            data: JSON.stringify(this.properties())
        }).done(function (properties) {
            utils.growlAlert('Successfully saved cloud account properties!', 'success');
        }).fail(function (jqxhr) {
            var message;
            try {
                var resp = JSON.parse(jqxhr.responseText);
                message = resp.properties.join('<br>');
            } catch (e) {
                message = 'Oops... there was a server error.'
            }
            message += '  Your properties were not saved.';
            utils.growlAlert(message, 'danger');
        });
    };

    CloudAccount.prototype.loadHostDefinitions = function () {
        var self = this;

        var tmpHostDefs = [];

        // Probably not the best way to do this, but I don't anticipate a cloud account having more
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

    CloudAccount.prototype.save = function () {
        var self = this;
        var keys = ['title', 'description', 'create_security_groups'];

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
                create_security_groups: self.createSecurityGroups()
            })
        }).done(function (account) {
            utils.growlAlert('Successfully saved cloud account!', 'success');
            try {
                self.parent.accountTitle(account.title);
            } catch (e) {}
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'cloud account', keys);
        });
    };

    CloudAccount.prototype.delete = function () {
        var self = this;
        var accountTitle = this.title();
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + accountTitle + '</strong>',
            message: 'Are you sure you want to delete <strong>' + accountTitle + '</strong>?',
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
                        if (window.location.pathname !== '/accounts/') {
                            window.location = '/accounts/';
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
                            title: 'Error deleting cloud account',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return CloudAccount;
});