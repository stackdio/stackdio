define([
    'q', 
    'knockout', 
    'util/postOffice',
    'model/models',
    'store/stores',
    'api/api'
],
function (Q, ko, _O_, models, stores, API) {
    API.Users.load()
        .then(function (key) {
            $("#public_key").val(key);
        });

    API.InstanceSizes.load();
    API.Formulae.load();
    API.Zones.load();

    // Define all data loading functions
    var dataLoaders = [API.ProviderTypes.load, API.Accounts.load, API.Profiles.load, 
                       API.Snapshots.load, API.Blueprints.load, API.Stacks.load];

    // Execute each data loader
    var dataLoaded = dataLoaders.reduce( function (loadData, next) {
        return loadData.then(next);
    }, Q([])).then(function () {
        // Convert select elements to the nice Bootstrappy style
        $('.selectpicker').selectpicker();

        // Specify a flattened array of Blueprint name as the store for the typeahead on the welcome page
        $('#blueprint_search').typeahead({
            name: 'blueprints',
            local: stores.Blueprints().map(function (b) {return b.title; }),
            limit: 10
        }).on('typeahead:selected', function (object, selectedItem) {
            var foundBlueprint = _.findWhere(stores.Blueprints(), { title: $('#blueprint_search').val() });
            self.launchStack(foundBlueprint);
        });

        // When user presses enter in the Launch Blueprint typeahead, start the process of launching a Stack
        $("#blueprint_search").keypress(function (evt) {
            if (evt.keyCode === 13) {
                var foundBlueprint = _.findWhere(stores.Blueprints(), { title: $('#blueprint_search').val() });
                self.launchStack(foundBlueprint);
            }
        });
        
        _O_.publish('all.updated', { update: true });
    })
    .catch(function (error) {
        // Handle any error from all above steps
        console.error(error.name, error.message);
    }).done();

});
