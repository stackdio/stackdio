
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

    // Define the cloud image model.
    function CloudImage(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/cloud/images/' + raw + '/'
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
        this.imageId = ko.observable();
        this.defaultInstanceSize = ko.observable();
        this.sshUser = ko.observable();

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    CloudImage.constructor = CloudImage;

    CloudImage.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.slug(raw.slug);
        this.imageId(raw.image_id);
        this.defaultInstanceSize(raw.default_instance_size);
        this.sshUser(raw.ssh_user);
    };

    // Reload the current cloud image
    CloudImage.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (image) {
            self.raw = image;
            self._process(image);
        });
    };

    CloudImage.prototype.save = function () {
        var self = this;
        var keys = ['title', 'description', 'image_id', 'default_instance_size', 'ssh_user'];

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
                image_id: self.imageId(),
                default_instance_size: self.defaultInstanceSize(),
                ssh_user: self.sshUser()
            })
        }).done(function (image) {
            utils.growlAlert('Successfully saved cloud image!', 'success');
            try {
                self.parent.imageTitle(image.title);
            } catch (e) {}
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'cloud image', keys);
        });
    };

    CloudImage.prototype.delete = function () {
        var self = this;
        var imageTitle = this.title();
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + imageTitle + '</strong>',
            message: 'Are you sure you want to delete <strong>' + imageTitle + '</strong>?',
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
                        if (window.location.pathname !== '/images/') {
                            window.location = '/images/';
                        } else if (self.parent && typeof self.parent.reload === 'function') {
                            self.parent.reload();
                        }
                    }).fail(function (jqxhr) {
                        var message;
                        try {
                            var resp = JSON.parse(jqxhr.responseText);
                            message = resp.detail.join('<br>');
                            if (Object.keys(resp).indexOf('blueprints') >= 0) {
                                message += '<br><br>Blueprints:<ul><li>' + resp.blueprints.join('</li><li>') + '</li></ul>';
                            }
                        } catch (e) {
                            message = 'Oops... there was a server error.  This has been reported ' +
                                'to your administrators.';
                        }
                        bootbox.alert({
                            title: 'Error deleting cloud image',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return CloudImage;
});