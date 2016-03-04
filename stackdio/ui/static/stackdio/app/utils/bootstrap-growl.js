
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
/**
 * Adapted from bootstrap-growl (https://github.com/ifightcrime/bootstrap-growl)
 */

((function (root, factory) {

    // CommonJS
    if (typeof exports === 'object') {
        module.exports = factory(require('jquery', 'bootstrap'));
    }
    // AMD module
    else if (typeof define === 'function' && define.amd) {
        define(['jquery', 'bootstrap'], factory);
    }

})(this, function ($) {
    $.bootstrapGrowl = function (message, options) {
        var $alert, css, offsetAmount;

        options = $.extend({}, $.bootstrapGrowl.default_options, options);
        $alert = $("<div>");
        $alert.attr("class", "bootstrap-growl alert");
        if (options.type) {
            $alert.addClass("alert-" + options.type);
        }
        if (options.allow_dismiss) {
            $alert.append('<a class="close" data-dismiss="alert" href="#">&times;</a>');
        }
        $alert.append(message);

        var mobile = $(window).width() <= 767;

        if (mobile) {
            offsetAmount = 63;
        } else {
            offsetAmount = -10;
        }
        $(".bootstrap-growl").each(function() {
            return offsetAmount = Math.max(offsetAmount, parseInt($(this).css('top')) + $(this).outerHeight() + options.stackup_spacing);
        });
        css = {
            "position": mobile ? "fixed" : "absolute",
            "margin": "0",
            "z-index": 9999,
            "display": "none",
            "width": options.width,
            "max-width": $(window).width() - 50,
            "top": offsetAmount + "px",
            "right": "25px"
        };
        $alert.css(css);
        $(options.ele).append($alert);
        $alert.fadeIn();
        if (options.delay > 0) {
            return $alert.delay(options.delay).fadeOut(function () {
                return $(this).remove();
            });
        }
    };

    $.bootstrapGrowl.default_options = {
        ele: "body",
        type: null,
        align: "right",
        width: "100%",
        delay: 4000,
        allow_dismiss: true,
        stackup_spacing: 10
    };

}));
