define(function () {
    return {
        showMessage : function (id, content, autohide, delay) {
            var timeout = (autohide && typeof delay === 'undefined') ? 3000 : delay;
            if (typeof content !== 'undefined' && content !== '') $(id+'-content').append(content);
            $(id).removeClass('hide');
            if (autohide) setTimeout(function () { $(id).addClass('hide'); $(id+'-content').empty(); }, timeout);
        }
    };
});
