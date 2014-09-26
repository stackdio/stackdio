define(['util/galaxy', 'util/alerts', 'bootbox', 'store/Formulas', 'api/api'], function($galaxy, alerts, bootbox, FormulaStore, API) {
    var ret = {
        updateFormula: function (formula) {
            if (formula.private_git_repo) {
                bootbox.dialog({
                    title: "Enter your git password:",
                    message: '<form class="bootbox-form"><input class="bootbox-input bootbox-input-text form-control" autocomplete="off" type="password" id="git_password_for_update"></form>',
                    buttons: {
                        cancel: {
                            label: "Cancel",
                            className: "btn-default",
                            callback: function () {
                                // Do nothing
                            }
                        },
                        success: {
                            label: "OK",
                            className: "btn-primary",
                            callback: function () {
                                git_password = $('#git_password_for_update').val();
                                ret.doUpdate(formula, git_password);
                            }
                        }
                    }
                });
            } else {
                ret.doUpdate(formula, '');
            }
        },
        doUpdate: function (formula, git_password) {
            API.Formulas.updateFromRepo(formula, git_password).then(function () {
                alerts.showMessage('#success', 'Formula successfully updated from repository.', true);
                FormulaStore.populate(true).then(function () {}).catch(function (err) { console.error(err); } ).done();
            }).catch(function (error) {
                alerts.showMessage('#error', 'There was an error while updating your formula. ' + error, true, 4000);
            }).done();
        }

    };

    return ret;
});