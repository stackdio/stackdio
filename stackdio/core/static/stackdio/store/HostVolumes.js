define(['store/store'], function (store) {
    var HostVolumes = function () {
        this.proxy = null;
    }

    HostVolumes.prototype = new store();
    HostVolumes.prototype.constructor = HostVolumes;

    return new HostVolumes();
});
