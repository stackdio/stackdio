define(["knockout",
        "q", 
        "viewmodel/abstract",
        "util/postOffice",
        "model/models",
        "store/stores",
        "api/api"], 
    function (ko, Q, abstract, _O_, models, stores, API) {

        var vm = function () {
            var self = this;

            self.search = function (model, evt) {
                API.Search.search($('#omnibox_search').val())
                    .then(function (matches) {
                        console.log(matches);
                    });
            };

            _O_.subscribe('*.updated', function (data) {
                var flattened = [].concat(stores.Blueprints(), stores.Stacks(), stores.Formulae());
                flattened.forEach(function (a) {
                    if (a instanceof models.Blueprint) {
                        a.type = 'Blueprint';
                        a.href = '';
                    } else if (a instanceof models.Stack) {
                        a.type = 'Stack';
                        a.href = '';
                    } else if (a instanceof models.Formula) {
                        a.type = 'Formula';
                        a.href = '';
                    } else {
                        a.type = 'Unknown';
                        a.href = '';
                    }
                });

                console.log('creating typeahead');

                $('#omnibox_search').typeahead({
                    name: 'search',
                    valueKey: 'title',
                    engine: _,
                    template: '<div class="search-result-<%= type %>"><%= type %> | <%= title %></div>',
                    local: flattened,
                    limit: 10
                });
            });

        };

        vm.prototype = new abstract();
        return vm;
});
