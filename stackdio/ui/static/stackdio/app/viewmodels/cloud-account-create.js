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
    'select2'
], function ($, ko, bootbox, utils) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Cloud Accounts',
                href: '/accounts/'
            },
            {
                active: true,
                title: 'New'
            }
        ];

        // Create the provider selector
        self.providerSelector = $('#accountProvider');
        self.regionSelector = $('#accountRegion');
        self.vpcSelector = $('#accountVpcId');
        self.sgSelector = $('#accountSecurityGroups');
        self.newsgSelector = $('#accountSecurityGroupsNew');

        self.providerSelector.select2({
            ajax: {
                url: '/api/cloud/providers/',
                dataType: 'json',
                delay: 100,
                data: function (params) {
                    return {
                        name: params.term
                    };
                },
                processResults: function (data) {
                    data.results.forEach(function (provider) {
                        provider.text = provider.name;
                        provider.id = provider.name;
                    });
                    return data;
                },
                cache: true
            },
            theme: 'bootstrap',
            placeholder: 'Select a provider...',
            templateResult: function (provider) {
                if (provider.loading) {
                    return provider.text;
                }
                return provider.name;
            },
            minimumInputLength: 0
        });

        self.regionSelector.select2({
            data: [],
            theme: 'bootstrap',
            placeholder: 'Select a region...',
            disabled: true
        });

        self.providerSelector.on('select2:select', function(ev) {
            var provider = ev.params.data;

            self.provider(provider);

            self.regionSelector.select2({
                ajax: {
                    url: provider.regions,
                    dataType: 'json',
                    delay: 100,
                    data: function (params) {
                        return {
                            title: params.term
                        };
                    },
                    processResults: function (data) {
                        data.results.forEach(function (provider) {
                            provider.text = provider.title;
                            provider.id = provider.title;
                        });
                        return data;
                    },
                    cache: true
                },
                theme: 'bootstrap',
                disabled: false,
                placeholder: 'Select a region...',
                templateResult: function (provider) {
                    if (provider.loading) {
                        return provider.text;
                    }
                    return provider.title;
                },
                minimumInputLength: 0
            });
        });

        self.regionSelector.on('select2:select', function (ev) {
            var region = ev.params.data;

            self.region(region.title);
        });

        self.sgSelector.select2({
            data: [],
            theme: 'bootstrap',
            placeholder: 'Select a security group...',
            disabled: true
        });

        self.newsgSelector.select2({
            data: [],
            theme: 'bootstrap',
            disabled: true
        });

        self.wizard = $('#accountWizard');

        self.wizard.on('actionclicked.fu.wizard', function (ev, data) {
            if (data.direction !== 'next') {
                return;
            }

            self.removeErrors(self.keys);

            var error = false;

            switch (data.step) {
                case 1:
                    // Basics
                    if (!self.provider()) {
                        utils.addError('#provider', ['May not be blank']);
                        error = true;
                    }

                    if (!self.title()) {
                        utils.addError('#title', ['May not be blank']);
                        error = true;
                    }

                    if (self.vpcEnabled() && !self.vpcId()) {
                        utils.addError('#vpc_id', ['May not be blank']);
                        error = true;
                    }

                    if (!self.region()) {
                        utils.addError('#region', ['May not be blank']);
                        error = true;
                    }

                    if (!error && self.previousProvider !== self.provider().name) {
                        self.previousProvider = self.provider().name;

                        $.ajax({
                            method: 'GET',
                            url: self.provider().required_fields
                        }).done(function (fields) {
                            var extras = [];
                            fields.forEach(function (field) {
                                if (field !== 'private_key') {
                                    var fieldObj = {
                                        apiName: field,
                                        displayName: self.extrasMap[field],
                                        fieldValue: ko.observable()
                                    };

                                    if (field === 'secret_access_key') {
                                        fieldObj.type = 'password';
                                    } else {
                                        fieldObj.type = 'text';
                                    }

                                    extras.push(fieldObj);
                                }
                            });
                            self.extraFields(extras);
                        });
                    }

                    break;

                case 2:
                    // Extras

                    // We have all the data now, create the account.  If it fails, go back to
                    // first page
                    self.createCloudAccount().done(function (account) {
                        self.selectedAccount = account;
                        self.makeSGSelector(account);
                    }).done(function () {
                        self.wizard.wizard('selectedItem', {step: 3});
                    }).fail(function (jqxhr) {
                        try {
                            var resp = JSON.parse(jqxhr.responseText);
                            var firstPage = false;
                            self.keys.forEach(function (key) {
                                if (resp.hasOwnProperty(key)) {
                                    firstPage = true;
                                }
                            });
                            if (firstPage) {
                                self.wizard.wizard('selectedItem', {step: 1});
                            } else {
                                self.wizard.wizard('selectedItem', {step: 2});
                            }
                        } catch (e) {
                            self.wizard.wizard('selectedItem', {step: 1});
                        }
                    });

                    // Do this so we don't have weird jumping around
                    ev.preventDefault();

                    break;

                case 3:
                    // Security Groups

                    var groups = self.sgSelector.select2('data');
                    var newGroups = self.newsgSelector.select2('data');

                    console.log(groups);
                    console.log(newGroups);

                    var ajaxList = [];

                    groups.forEach(function (group) {
                        ajaxList.push($.ajax({
                            method: 'POST',
                            url: self.selectedAccount.security_groups,
                            data: JSON.stringify({
                                'group_id': group.group_id,
                                'default': true
                            })
                        }));
                    });

                    newGroups.forEach(function (group) {
                        ajaxList.push($.ajax({
                            method: 'POST',
                            url: self.selectedAccount.security_groups,
                            data: JSON.stringify({
                                'name': group.text,
                                'default': true
                            })
                        }));
                    });

                    $.when.apply(this, ajaxList).done(function () {
                        window.location = '/accounts/';
                    }).fail(function (jqxhr) {
                        utils.alertError(jqxhr, 'Error saving permissions');
                    });

                    break;
            }

            if (error) {
                ev.preventDefault();
            }
        });

        self.keys = ['provider', 'title', 'description',
            'create_security_groups', 'vpc_id', 'region'];

        self.extrasMap = {
            access_key_id: 'Access Key ID',
            secret_access_key: 'Secret Access Key',
            keypair: 'Keypair Name',
            private_key: 'Private Key',
            route53_domain: 'Route 53 Domain'
        };

        self.previousProvider = null;

        // View variables
        self.provider = ko.observable();
        self.title = ko.observable();
        self.description = ko.observable();
        self.vpcEnabled = ko.observable();
        self.vpcId = ko.observable();
        self.region = ko.observable();
        self.createSecurityGroups = ko.observable();
        self.privateKey = ko.observable();

        self.extraFields = ko.observableArray([]);
        self.securityGroups = ko.observableArray([]);
        self.selectedAccount = null;

        self.sgSubscription = null;
        self.vpcSubscription = null;

        self.makeSGSelector = function (account) {
            self.sgSelector.select2({
                ajax: {
                    url: account.all_security_groups,
                    dataType: 'json',
                    delay: 100,
                    data: function (params) {
                        return {
                            name: params.term
                        };
                    },
                    processResults: function (data) {
                        var realData = [];
                        data.results.forEach(function (group) {
                            group.text = group.name;
                            group.id = group.name;
                            realData.push(group);
                        });
                        return { results: realData };
                    },
                    cache: true
                },
                theme: 'bootstrap',
                disabled: false,
                placeholder: 'Select a security group...',
                minimumInputLength: 0
            });

            self.newsgSelector.select2({
                theme: 'bootstrap',
                tags: true,
                tokenSeparators: [',']
            });
        };

        // Necessary functions
        self.reset = function() {
            // Make sure we don't have more than 1 subscription
            if (self.sgSubscription) {
                self.sgSubscription.dispose();
            }

            if (self.vpcSubscription) {
                self.vpcSubscription.dispose();
            }

            var $sg = $('#sg-checkbox');
            self.sgSubscription = self.createSecurityGroups.subscribe(function (newVal) {
                if (newVal) {
                    $sg.checkbox('check');
                } else {
                    $sg.checkbox('uncheck');
                }
            });

            var $vpc = $('#vpc-checkbox');
            self.vpcSubscription = self.vpcEnabled.subscribe(function (newVal) {
                if (newVal) {
                    $vpc.checkbox('check');
                } else {
                    $vpc.checkbox('uncheck');
                }
            });

            self.provider(null);
            self.title('');
            self.description('');
            self.vpcEnabled(true);
            self.createSecurityGroups(true);
            self.vpcId('');
            self.region(null);
            self.extraFields([]);
            self.securityGroups([]);
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.createCloudAccount = function() {
            var keys = self.keys.slice();

            var createData = {
                provider: self.provider().name,
                title: self.title(),
                description: self.description(),
                create_security_groups: self.createSecurityGroups(),
                private_key: self.privateKey(),
                region: self.region()
            };

            if (self.vpcEnabled()) {
                createData.vpc_id = self.vpcId();
            } else {
                createData.vpc_id = '';
            }

            self.extraFields().forEach(function (field) {
                createData[field.apiName] = field.fieldValue();
                keys.push(field.apiName);
            });

            // First remove all the old error messages
            self.removeErrors(keys);

            // Create the account!
            return $.ajax({
                'method': 'POST',
                'url': '/api/cloud/accounts/',
                'data': JSON.stringify(createData)
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
                                        el.append('<span class="help-block">An account with this title already exists.</span>');
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
                        title: 'Error creating account',
                        message: message
                    });
                }
            });
        };

        self.reset();
    };
});
