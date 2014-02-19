define(['q', 'api/Root', 'settings'],
function (Q, RootAPI, settings) {
    // API.Users.load().then(function (key) {
    //     $("#public_key").val(key);
    // });

    // API.InstanceSizes.load();
    // API.Formulae.load();
    // API.Zones.load();

    RootAPI.load().then(function () {
        console.log(settings.api);
    }).catch(function (error) {
        console.error(error.name, error.message);
    });

    // ProviderTypeStore.populate().then(function () {
    //     console.log('types', ProviderTypeStore.collection);
    // });

    // SnapshotStore.populate().then(function () {
    //     console.log('snapshots', SnapshotStore.collection);
    // });



    // // Execute each data loader
    // var dataLoaded = dataLoaders.reduce(function (loadData, next) {
    //     return loadData.then(next);
    // }, Q([])).then(function () {
    //     // Convert select elements to the nice Bootstrappy style
    //     // $('.selectpicker').selectpicker();


        
    //     _O_.publish('all.updated', { update: true });
    // })
    // .catch(function (error) {
    //     // Handle any error from all above steps
    //     console.error(error.name, error.message);
    // }).done();

});
