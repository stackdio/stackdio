
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
    'knockout'
], function ($, ko) {
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
        this.default(raw.is_default);
        this.managed(raw.is_managed);
    };

    // Reload the current volume
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

    return SecurityGroup;
});