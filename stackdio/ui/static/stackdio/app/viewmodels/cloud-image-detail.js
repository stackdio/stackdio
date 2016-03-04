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
    'models/cloud-image',
    'models/cloud-account',
    'select2'
], function($, ko, CloudImage, CloudAccount) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.image = null;
        self.account = null;

        self.imageUrl = ko.observable('');

        self.accountTitle = ko.observable();
        self.accountUrl = '/accounts/' + window.stackdio.accountId + '/';

        self.accountId = ko.observable('');

        // Override the breadcrumbs
        if (document.referrer.indexOf('account') >= 0) {
            self.breadcrumbs = [
                {
                    active: false,
                    title: 'Cloud Accounts',
                    href: '/accounts/'
                },
                {
                    active: false,
                    title: window.stackdio.accountTitle,
                    href: ko.computed(function () { return '/accounts/' + self.accountId() + '/';})
                },
                {
                    active: false,
                    title: 'Images',
                    href: ko.computed(function () { return '/accounts/' + self.accountId() + '/images/';})
                },
                {
                    active: true,
                    title: window.stackdio.imageTitle
                }
            ];
        } else {
            self.breadcrumbs = [
                {
                    active: false,
                    title: 'Cloud Images',
                    href: '/images/'
                },
                {
                    active: true,
                    title: window.stackdio.imageTitle
                }
            ];
        }

        self.sizeSelector = $('#imageDefaultInstanceSize');

        self.sizeSelector.select2({
            ajax: {
                url: '/api/cloud/providers/' + window.stackdio.providerName + '/instance_sizes/',
                dataType: 'json',
                delay: 100,
                data: function (params) {
                    return {
                        instance_id: params.term
                    };
                },
                processResults: function (data) {
                    data.results.forEach(function (size) {
                        size.id = size.instance_id;
                        size.text = size.instance_id;
                    });
                    return data;
                },
                cache: true
            },
            theme: 'bootstrap',
            placeholder: 'Select an instance size...',
            minimumInputLength: 0
        });

        self.sizeSelector.on('select2:select', function (ev) {
            var size = ev.params.data;

            self.image.defaultInstanceSize(size.instance_id);
        });

        self.reset = function() {
            // Create the image object.  Pass in the image id, and let the model load itself.
            self.image = new CloudImage(window.stackdio.imageId, self);
            self.account = new CloudAccount(window.stackdio.accountId, self);
            self.image.waiting.done(function () {
                document.title = 'stackd.io | Cloud Image Detail - ' + self.image.title();
                self.accountId(self.image.raw.account);

                // Set the default size
                var size = self.image.defaultInstanceSize();
                // We have to add it into the DOM before we can select it programmatically
                self.sizeSelector.append('<option value="' + size + '" title="' + size + '">' + size + '</option>');
                self.sizeSelector.val(size).trigger('change');
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/images/';
            });
            self.account.waiting.done(function () {
                self.accountTitle(self.account.title() + '  --  ' + self.account.description());
            });
        };

        // Start everything up
        self.reset();
    };
});