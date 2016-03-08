
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
    'bootbox',
    'utils/bootstrap-growl'
], function(bootbox) {
    'use strict';

    return {
        addError: function  (el, msgs) {
            var $el = $(el);
            $el.addClass('has-error');
            msgs.forEach(function (errMsg) {
                $el.append('<span class="help-block">' + errMsg + '</span>');
            });
        },
        growlAlert: function (message, type) {
            $.bootstrapGrowl(message, {
                ele: '#main-content',
                width: '450px',
                type: type
            });
        },
        alertError: function (jqxhr, title, customMessage) {
            var message;
            try {
                var resp = JSON.parse(jqxhr.responseText);
                message = '';
                for (var key in resp) {
                    if (resp.hasOwnProperty(key)) {
                        var betterKey = key.replace('_', ' ');

                        resp[key].forEach(function (errMsg) {
                            message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                        });
                    }
                }
                message = '<dl class="dl-horizontal">' + message + '</dl>';
                if (customMessage) {
                    message = customMessage + message;
                }
            } catch (e) {
                message = 'Oops... there was a server error.  This has been reported ' +
                    'to your administrators.';
            }
            bootbox.alert({
                title: title,
                message: message
            });
        },
        parseSaveError: function (jqxhr, modelName, keys) {
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
                                    el.append('<span class="help-block">A ' + modelName + ' with this title already exists.</span>');
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
                    'your administrators.'
            }
            if (message) {
                bootbox.alert({
                    title: 'Error saving ' + modelName,
                    message: message
                });
            }
        }
    };
});