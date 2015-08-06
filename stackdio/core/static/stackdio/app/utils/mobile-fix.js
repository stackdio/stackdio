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

    if (typeof require === "function") {
        // Load with require
        require(['jquery'], function ($) {
            console.log('loading with require...');
            $(document).ready(mobileFix)
        });
    } else {
        console.log('Not using require');
        $(document).ready(mobileFix);
    }
})(window);