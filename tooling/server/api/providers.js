Meteor.startup(function () {
    var require = __meteor_bootstrap__.require;


    // ######################################################
    //      P R O V I D E R S
    // ######################################################
    Providers = new Meteor.Collection("providers");

    // Get the list of providers in the system
    Meteor.http.get('http://localhost:8000/api/providers/', 
        {
            headers: {
                'Accept': 'application/json'
            },
            auth: 'testuser:password'
        },
        function (error, response) {
            var p, provider, providers = JSON.parse(response.content).results;

            // Clear the providers collection
            Providers.remove({});

            // Insert all providers from the API into the collection
            for (p in providers) {
                provider = providers[p];
                Providers.insert(provider);
            }

            // Publish the providers in the all-providers channel
            // Meteor.publish("all-providers", function () {
            //     return Providers.find(); // everything
            // });

        }
    );

});