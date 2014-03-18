define(['knockout', 'q', 'util/galaxy', 'bootstrap-typeahead'],
function (ko, Q, $galaxy) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'search';
        self.templatePath = 'omnibox.html';
        self.domBindingId = '.omnibox';
        self.autoRender = true;

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.search = function (model, evt) {

        };

        $galaxy.network.subscribe(self.id + '.docked', function (data) {
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
                        $galaxy.transport({
                            location: 'formula.detail',
                            payload: {
                                formula: selectedItem.id
                            }
                        });
                        break;
                    case 'blueprint':
                        $galaxy.transport({
                            location: 'blueprint.detail',
                            payload: {
                                blueprint: selectedItem.id
                            }
                        });
                        break;
                    case 'stack':
                        $galaxy.transport({
                            location: 'stack.detail',
                            payload: {
                                stack: selectedItem.id
                            }
                        });
                        break;
                }
            });
        });
    };
    return new vm();
});
