
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
    'knockout'
], function ($, ko) {
    'use strict';

    // Define the volume model.
    function Volume(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/volumes/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Save the id
        this.id = raw.id;

        // Editable fields
        this.volumeId = ko.observable();
        this.snapshotId = ko.observable();
        this.size = ko.observable();
        this.device = ko.observable();
        this.mountPoint = ko.observable();
        this.encrypted = ko.observable();
        this.extraOptions = ko.observable();

        if (needReload) {
            this.reload();
        } else {
            this._process(raw);
        }
    }

    Volume.constructor = Volume;

    Volume.prototype._process = function (raw) {
        this.volumeId(raw.volume_id);
        this.snapshotId(raw.snapshot_id);
        this.size(raw.size_in_gb);
        this.device(raw.device);
        this.mountPoint(raw.mount_point);
        this.encrypted(raw.encrypted);
        this.extraOptions(raw.extra_options);
    };

    // Reload the current volume
    Volume.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (volume) {
            self.raw = volume;
            self._process(volume);
        });
    };

    return Volume;
});