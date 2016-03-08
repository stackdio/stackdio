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

(function(window, undefined) {
    'use strict';

    // Code snippet from jQuery.stayInWebApp plugin by mrmoses (https://github.com/mrmoses/jQuery.stayInWebApp)
    // *Written so it works with or without using require()*
    function mobileFix() {
        if(("standalone" in window.navigator) && window.navigator.standalone) {
            var sel = 'a';
            $("body").delegate(sel, "click", function(e) {
                if($(this).attr("target") == undefined || $(this).attr("target") == "" || $(this).attr("target") == "_self") {
                    var d = $(this).attr("href");
                    if(!d.match(/^http(s?)/g)) { e.preventDefault(); self.location = d; }
                }
            });
        }
    }

    // Load properly with require if necessary
    if (typeof require === "function") {
        // Load with require
        require(['jquery'], function ($) {
            $(document).ready(mobileFix)
        });
    } else {
        $(document).ready(mobileFix);
    }
})(window);