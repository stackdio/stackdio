define(['store/store'], function (store) {
    var HostAccessRules = function () {
        this.proxy = null;
    }

    HostAccessRules.prototype = new store();
    HostAccessRules.prototype.constructor = HostAccessRules;

    return new HostAccessRules();
});
