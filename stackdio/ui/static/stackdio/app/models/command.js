
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
    'moment'
], function ($, ko, moment) {
    'use strict';

    function FakeMoment () {
        this.calendar = function () {
            return '';
        };

        this.toString = function () {
            return '';
        };
    }

    // Define the command model.
    function Command(raw, parent) {
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
        this.downloadUrl = ko.observable();
        this.submitTime = ko.observable(new FakeMoment());
        this.startTime = ko.observable(new FakeMoment());
        this.finishTime = ko.observable(new FakeMoment());
        this.status = ko.observable();
        this.labelClass = ko.observable();
        this.hostTarget = ko.observable();
        this.command = ko.observable();
        this.stdout = ko.observable();
        this.stderr = ko.observable();

        if (needReload) {
            this.reload();
        } else {
            this._process(raw);
        }
    }

    Command.constructor = Command;

    function processTime(time) {
        if (time.length) {
            return moment(time);
        } else {
            return new FakeMoment();
        }
    }

    Command.prototype._process = function (raw) {
        this.downloadUrl(raw.zip_url);

        // Moment-ize the dates
        this.submitTime(processTime(raw.submit_time));
        this.startTime(processTime(raw.start_time));
        this.finishTime(processTime(raw.finish_time));
        this.status(raw.status);
        this.hostTarget(raw.host_target);
        this.command(raw.command);
        this.stdout(raw.std_out);
        this.stderr(raw.std_err);

        switch (raw.status) {
            case 'finished':
                this.labelClass('label-success');
                break;
            case 'running':
                this.labelClass('label-warning');
                break;
            case 'pending':
            case 'waiting':
                this.labelClass('label-info');
                break;
            default:
                this.labelClass('label-default');
        }
    };

    // Reload the current volume
    Command.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (command) {
            self.raw = command;
            self._process(command);
        });
    };

    Command.prototype.delete = function () {
        $.ajax({
            method: 'DELETE',
            url: this.raw.url
        })
    };

    return Command;
});