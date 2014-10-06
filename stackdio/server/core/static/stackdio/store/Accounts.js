define(['store/store', 'api/Accounts'], function (store, API) {
    var Accounts = function () {
        this.proxy = API;
    }

    Accounts.prototype = new store();
    Accounts.prototype.constructor = Accounts;

    return new Accounts();
});
