define(['store/store', 'api/Stacks'], function (store, API) {
    var Stacks = function () {
        this.proxy = API;
    }

    Stacks.prototype = new store();
    Stacks.prototype.constructor = Stacks;

    return new Stacks();
});
