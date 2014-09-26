define(['store/store'], function (store) {
    var FormulaComponents = function () {
        this.proxy = null;
    }

    FormulaComponents.prototype = new store();
    FormulaComponents.prototype.constructor = FormulaComponents;

    return new FormulaComponents();
});
