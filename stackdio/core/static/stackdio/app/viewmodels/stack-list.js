
function StackListViewModel() {
    var self = this;

    self.previousPage = ko.observable();
    self.nextPage = ko.observable();
    self.count = ko.observable();
    self.stacks = ko.observableArray([]);

    self.reloadStacks = function () {
        $.getJSON('/api/stacks/', function(stacks) {
            self.count(stacks.count);
            self.previousPage(stacks.previous);
            self.nextPage(stacks.next);

            var convertedList = [];
            stacks.results.forEach(function(stack) {
                convertedList.push(ko.mapping.fromJS(stack));
            });
            self.stacks(convertedList);
        });
    };

    setInterval(self.reloadStacks, 3000);
}

ko.applyBindings(new StackListViewModel());
