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
    'ladda',
    'bootbox',
    'select2'
], function ($, ko, Ladda, bootbox) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Snapshots',
                href: '/snapshots/'
            },
            {
                active: true,
                title: 'New'
            }
        ];

        // Create the account selector
        self.accountSelector = $('#snapshotAccount');

        self.accountSelector.select2({
            ajax: {
                url: '/api/cloud/accounts/',
                dataType: 'json',
                delay: 100,
                data: function (params) {
                    return {
                        title: params.term
                    };
                },
                processResults: function (data) {
                    data.results.forEach(function (account) {
                        account.text = account.title;
                    });
                    return data;
                },
                cache: true
            },
            theme: 'bootstrap',
            placeholder: 'Select an account...',
            templateResult: function (account) {
                if (account.loading) {
                    return account.text;
                }
                return account.title + '  --  ' + account.description;
            },
            minimumInputLength: 0
        });

        self.accountSelector.on('select2:select', function(ev) {
            var account = ev.params.data;
            self.accountId(account.id);
        });

        // View variables
        self.accountId = ko.observable();
        self.title = ko.observable();
        self.description = ko.observable();
        self.snapshotId = ko.observable();
        self.filesystemType = ko.observable();

        // Necessary functions
        self.reset = function() {
            self.accountId(null);
            self.title('');
            self.description('');
            self.snapshotId('');
            self.filesystemType('');
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.createSnapshot = function() {
            // First remove all the old error messages
            var keys = ['account', 'title', 'description', 'snapshot_id', 'filesystem_type'];

            self.removeErrors(keys);

            // Grab both button objects
            var createButton = Ladda.create(document.querySelector('#create-button'));

            // Start them up
            createButton.start();

            // Create the snapshot!
            $.ajax({
                'method': 'POST',
                'url': '/api/cloud/snapshots/',
                'data': JSON.stringify({
                    account: self.accountId(),
                    title: self.title(),
                    description: self.description(),
                    snapshot_id: self.snapshotId(),
                    filesystem_type: self.filesystemType()
                })
            }).always(function () {
                // Stop our spinning buttons FIRST
                createButton.stop();
            }).done(function () {
                // Successful creation - just redirect to the main snapshots page
                window.location = '/snapshots/';
            }).fail(function (jqxhr) {
                // Display any error messages
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
                                    if (errMsg.indexOf('title') >= 0) {
                                        var el = $('#title');
                                        el.addClass('has-error');
                                        el.append('<span class="help-block">A snapshot with this title already exists.</span>');
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
                        'your administrators.';
                }
                if (message) {
                    bootbox.alert({
                        title: 'Error creating snapshot',
                        message: message
                    });
                }
            });
        };

        self.reset();
    };
});
