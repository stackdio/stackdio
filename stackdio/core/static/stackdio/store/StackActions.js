define(['store/store'], function (store) {
        var StackActions = function () {
            this.proxy = null;
        }

        StackActions.prototype = new store();
        StackActions.prototype.constructor = StackActions;

        return new StackActions();
});



