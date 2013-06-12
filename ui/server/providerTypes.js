Meteor.startup(function () {

    // ######################################################
    //      P R O V I D E R   A C C O U N T S
    // ######################################################
    ProviderTypes = new Meteor.Collection("providerTypes");

    // Get the list of ProviderTypes in the system
    Meteor.http.get('http://localhost:8000/api/provider_types/', 
        {
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password')
            }
        },
        function (error, response) {
            var i, item, items = response.data.results;

            // Clear the ProviderTypes collection
            ProviderTypes.remove({});

            // Insert all ProviderTypes from the API into the collection
            for (i in items) {
                item = items[i];
                ProviderTypes.insert(item);
            }
        }
    );

});