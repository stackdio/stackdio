define(['store/store', 'api/StackHosts'], function (store, API) {
    var StackHosts = function () {
        this.proxy = API;
    }

    StackHosts.prototype = new store();
    StackHosts.prototype.constructor = StackHosts;

    return new StackHosts();
});
