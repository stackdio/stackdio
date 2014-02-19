define(['store/store', 'api/Formulas'], function (store, API) {
    var Formulas = function () {
        this.proxy = API;
    }

    Formulas.prototype = new store();
    Formulas.prototype.constructor = Formulas;

    return new Formulas();
});
