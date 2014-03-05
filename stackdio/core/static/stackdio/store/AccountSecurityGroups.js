define(['store/store', 'api/SecurityGroups'], function (store, API) {
    var AccountSecurityGroups = function () {
        this.proxy = API;
    }

    AccountSecurityGroups.prototype = new store();
    AccountSecurityGroups.prototype.constructor = AccountSecurityGroups;

    return new AccountSecurityGroups();
});
