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

            };

            $('#omnibox_search').on('typeahead:selected', function (object, selectedItem) {
                switch (selectedItem.result_type) {
                    case 'formula':
                        _O_.publish('navigate', 'Formulas');
                        _O_.publish('formula.open', selectedItem);
                        break;
                    case 'blueprint':
                        _O_.publish('navigate', 'Blueprints');
                        _O_.publish('blueprint.open', selectedItem);
                        break;
                    case 'stack':
                        _O_.publish('navigate', 'Stacks');
                        _O_.publish('stack.open', selectedItem);
                        break;
                }
            });


            _O_.subscribe('*.updated', function (data) {
                $('#omnibox_search').typeahead({
                    name: 'search',
                    valueKey: 'title',
                    engine: _,
                    minLength: 1,
                    template: '<div class="search-result-<%= result_type %>"><%= result_type %> | <%= title %></div>',
                    // local: flattened,
                    remote: '/api/search/?q=%QUERY',
                    limit: 10
                });
            });

        };

        vm.prototype = new abstract();
        return vm;
});
