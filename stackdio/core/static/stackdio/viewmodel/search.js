define(["knockout",
        "q", 
        "viewmodel/abstract",
        "model/models",
        "store/stores",
        "api/api"], 
    function (ko, Q, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;

            self.search = function (model, evt) {
                API.Search.search($('#omnibox_search').val())
                    .then(function (matches) {
                        console.log(matches);
                    });
            };
        };

        vm.prototype = new abstractVM();
        return vm;
});
