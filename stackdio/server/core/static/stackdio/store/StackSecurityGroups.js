define(['store/store'], function (store) {
        var StackSecurityGroups = function () {
            this.proxy = null;
        }

        StackSecurityGroups.prototype = new store();
        StackSecurityGroups.prototype.constructor = StackSecurityGroups;

        return new StackSecurityGroups();
});



