define(['q', 'knockout', 'util/galaxy', 'api/api', 'util/form'],
function (Q, ko, $galaxy, API, formutils) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedAccount = ko.observable(null);


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'user.password';
        self.templatePath = 'user.password.html';
        self.domBindingId = '#user-password';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }

        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            API.Users.load().then(function (public_key) {
                $('#first_name').val(window.stackdio.user.first_name);
                $('#last_name').val(window.stackdio.user.last_name);
                $('#public_key').val(public_key);
            })
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */
        self.savePassword = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            if (record.new_password.value !== record.new_password_confirm.value) {
                self.showMessage('#password-error', 'Your new passwords do not match', true);
                return;
            }

            API.Users.savePassword(record.current_password.value, 
                                   record.new_password.value, 
                                   record.new_password_confirm.value)
                .then(function (error) {
                    if (typeof error !== 'undefined') {
                        self.showError();
                        return;
                    }

                    $('#current_password').val('');
                    $('#new_password').val('');
                    $('#new_password_confirm').val('');
                    self.showSuccess();
                });
        };

        self.showError = function () {
            $('#password-error').removeClass('hide');
            setTimeout("$('#password-error').addClass('hide')", 3000);
        };

        self.closeError = function () {
            $('#password-error').addClass('hide');
        };

    };
    return new vm();
});
