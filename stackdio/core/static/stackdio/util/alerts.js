define(function () {

    $('#clearError').click(function () {
        $('.alert').addClass('hide');
    });

    $('#clearSuccess').click(function () {
        $('.alert').addClass('hide');
    });

    return {
        showMessage : function (id, content, autohide, delay, action) {
            var timeout = (autohide && typeof delay === 'undefined') ? 3000 : delay;
            if (typeof content !== 'undefined' && content !== '') $(id+'-content').append(content);
            $(id).removeClass('hide');
            if (autohide) {
                setTimeout(function () {
                    $(id).addClass('hide');
                    $(id+'-content').empty();
                    if (action) {
                        action.call();
                    };
                }, timeout);
            }
        }
    };
});
