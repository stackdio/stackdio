
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
    'bootbox'
], function(bootbox) {
    'use strict';

    return {
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
        }
    };
});