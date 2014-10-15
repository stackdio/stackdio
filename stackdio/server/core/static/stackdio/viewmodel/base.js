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

define(['util/66'], function ($66) {
    return function baseViewModel () {
        var self = this;

        self.$66 = $66;
        self.isSuperUser = stackdio.settings.superuser;

        $galaxy.transport = function (options) {
            $66.navigate(options);
        };

        self.showSuccess = function () {
            $(".alert-success").removeClass('hide');
            setTimeout("$('.alert-success').addClass('hide')", 3000);
        };

        self.closeSuccess = function () {
            $(".alert-success").addClass('hide');
        };

        self.showMessage = function (id, content, autohide, delay) {
            var timeout = (autohide && typeof delay === 'undefined') ? 3000 : delay;
            if (typeof content !== 'undefined' && content !== '') $(id).append(content);
            $(id).removeClass('hide');
            if (autohide) setTimeout(function () { $(id).addClass('hide'); $(id).empty(); }, timeout);
        };

   }
});
