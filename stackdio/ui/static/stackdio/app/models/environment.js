
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

    // Define the environment model.
    function Environment(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                name: raw,
                url: '/api/environments/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Save the id
        this.id = raw.name;
        this.detailUrl = '/environments/' + this.id + '/';

        // Editable fields
        this.name = ko.observable();
        this.description = ko.observable();
        this.labelList = ko.observable();

        // Lazy-loaded properties (not returned from the main environment endpoint)
        this.properties = ko.observable({});
        this.formulaVersions = ko.observableArray([]);

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Environment.constructor = Environment;

    Environment.prototype._process = function (raw) {
        this.name(raw.name);
        this.description(raw.description);
        this.labelList(raw.label_list);
    };

    // Reload the current environment
    Environment.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (environment) {
            self.raw = environment;
            self._process(environment);
        });
    };

    // Lazy-load the properties
    Environment.prototype.loadProperties = function () {
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

    Environment.prototype.saveProperties = function () {
        $.ajax({
            method: 'PUT',
            url: this.raw.properties,
            data: JSON.stringify(this.properties())
        }).done(function (properties) {
            utils.growlAlert('Successfully saved environment properties!', 'success');
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

    Environment.prototype.save = function () {
        var self = this;
        var keys = ['name', 'description'];

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
                name: self.name(),
                description: self.description()
            })
        }).done(function (environment) {
            utils.growlAlert('Successfully saved environment!', 'success');
            try {
                self.parent.environmentName(environment.name);
            } catch (e) {}
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'environment', keys);
        });
    };

    Environment.prototype.delete = function () {
        var self = this;
        var environmentName = this.name();
        bootbox.confirm({
            name: 'Confirm delete of <strong>' + environmentName + '</strong>',
            message: 'Are you sure you want to delete <strong>' + environmentName + '</strong>?',
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
                        if (window.location.pathname !== '/environments/') {
                            window.location = '/environments/';
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
                            name: 'Error deleting environment',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Environment;
});