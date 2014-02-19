define(['store/store'], function (store) {
    var BlueprintHosts = function () {
        this.proxy = null;
    }

    BlueprintHosts.prototype = new store();
    BlueprintHosts.prototype.constructor = BlueprintHosts;

    return new BlueprintHosts();
});
