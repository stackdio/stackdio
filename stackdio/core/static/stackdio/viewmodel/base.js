define(['util/66'], function ($66) {
    return function baseViewModel () {
        var self = this;

        self.$66 = $66;
        self.isSuperUser = stackdio.settings.superuser;

        self.navigate = function (options) {
            $66.navigate(options);
        };

        self.showSuccess = function () {
            $(".alert-success").removeClass('hide');
            setTimeout("$('.alert-success').addClass('hide')", 3000);
        };

        self.closeSuccess = function () {
            $(".alert-success").addClass('hide');
        };
   }
});
