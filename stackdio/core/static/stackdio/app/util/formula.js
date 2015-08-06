/*!
  * Copyright 2014,  Digital Reasoning
  * 
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  * 
  *     http://www.apache.org/licenses/LICENSE-2.0
  * 
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  * 
*/

define(['util/galaxy', 'util/alerts', '../../bower_components/bootbox/bootbox', 'store/Formulas', 'api/api'], function($galaxy, alerts, bootbox, FormulaStore, API) {
    var ret = {
        updateFormula: function (formula) {
            if (formula.private_git_repo && !formula.access_token) {
                bootbox.dialog({
                    title: "Enter the git password for user " + formula.git_username + ":",
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