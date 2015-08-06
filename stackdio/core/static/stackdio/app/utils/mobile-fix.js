(function(window, undefined) {
    // Code snippet from jQuery.stayInWebApp plugin by mrmoses (https://github.com/mrmoses/jQuery.stayInWebApp)
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