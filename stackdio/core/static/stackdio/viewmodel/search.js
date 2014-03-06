define(['knockout', 'q', 'viewmodel/base', 'util/postOffice'],
function (ko, Q, base, _O_) {

    var vm = function () {
        var self = this;

        self.search = function (model, evt) {

        };

        self.$66.news.subscribe('*.updated', function (data) {
            $('#omnibox_search').typeahead({
                name: 'search',
                valueKey: 'title',
                engine: _,
                minLength: 1,
                template: '<div class="search-result-<%= result_type %>"><%= result_type %> | <%= title %></div>',
                remote: '/api/search/?q=%QUERY',
                limit: 10
            }).on('typeahead:selected', function (object, selectedItem) {
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
        });

    };

    vm.prototype = new abstract();
    return vm;
});
