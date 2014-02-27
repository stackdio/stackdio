define(["jquery"], function ($) {
    stackdio.settings = {};

    var getCookie = function (name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    stackdio.settings.pageSize = 15;
    stackdio.settings.csrftoken = getCookie('csrftoken');
    // stackdio.settings.superuser = (window.stackdio.user.admin === "True");

    // if (Object.hasOwnProperty('freeze')) {
    //     Object.freeze(stackdio.settings);
    // }

    return stackdio.settings;

});
