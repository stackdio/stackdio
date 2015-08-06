
define([
    'jquery',
    'knockout'
], function ($, ko) {
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
                self.stacks(stacks.results);
            });
        };

        self.deleteStack = function (stack) {
            $.ajax({
                method: 'DELETE',
                url: '/api/stacks/' + stack.id + '/',
                headers: {
                    Accept: 'application/json'
                }
            }).done(function (resp) {
                alert('deleting');
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.log(jqXHR);
                console.log(textStatus);
                console.log(errorThrown);
            });
        };

        setInterval(self.reloadStacks, 3000);
    }

    return new StackListViewModel();
});
