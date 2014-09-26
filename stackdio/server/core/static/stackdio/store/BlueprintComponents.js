define(['store/store'], function (store) {
    var BlueprintComponents = function () {
        this.proxy = null;
    }

    BlueprintComponents.prototype = new store();
    BlueprintComponents.prototype.constructor = BlueprintComponents;

    return new BlueprintComponents();
});
