
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
    'knockout',
    'bootbox',
    'underscore'
], function (ko, bootbox, _) {
    'use strict';

    // Define the label model.
    function Label(raw, parent) {
        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Editable fields
        this.key = ko.observable();
        this.value = ko.observable();

        this._process(raw);
    }

    Label.constructor = Label;


    Label.prototype._process = function (raw) {
        this.key(raw.key);
        this.value(raw.value);
    };

    Label.prototype.delete = function () {
        var self = this;
        var labelKey = _.escape(self.key());
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + labelKey + '</strong>',
            message: 'Are you sure you want to delete the label <strong>' + labelKey + '</strong>?',
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
                        if (self.parent.reload) {
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
                            title: 'Error deleting label',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Label;
});