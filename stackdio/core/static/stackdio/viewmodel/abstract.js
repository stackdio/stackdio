define(function () {

    return function abstractViewModel () {
        var self = this;

        /*
         *  ==================================================================================
         *  M E T H O D S
         *  ==================================================================================
         */
        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };

        self.showError = function (message, delay) {
            var timeout = (typeof delay === 'undefined') ? 3000 : delay;

            $("#alert-error-details").empty();
            $("#alert-error-details").append(message);
            $("#alert-error").show();
            setTimeout(function () { $("#alert-error").hide(); $("#alert-error-details").empty(); }, timeout);
        };

        self.closeSuccess = function () {
            $("#alert-success").hide();
        };
        
        self.showMessage = function (id, content, autohide, delay) {
            var timeout = (autohide && typeof delay === 'undefined') ? 3000 : delay;
            if (typeof content !== 'undefined' && content !== '') $(id).append(content);
            $(id).show();
            if (autohide) setTimeout(function () { $(id).hide(); $(id).empty(); }, timeout);
        };

        self.closeError = function () {
            $("#alert-error").hide();
            $("#alert-error-details").empty();
        };
        
   }
});