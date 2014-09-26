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
