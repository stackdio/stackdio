Meteor.startup(function () {

    // ######################################################
    //      P R O V I D E R S
    // ######################################################
    ProviderProfiles = new Meteor.Collection("providerProfiles");

    // Get the list of providers in the system
    Meteor.http.get('http://localhost:8000/api/profiles/', 
        {
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password')
            }
        },
        function (error, response) {
            var i, item, items = response.data.results;

            // Clear the providers collection
            ProviderProfiles.remove({});

            // Insert all providers from the API into the collection
            for (i in items) {
                item = items[i];
                ProviderProfiles.insert(item);
            }

        }
    );

});