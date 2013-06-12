Meteor.startup(function () {

    // ######################################################
    //      I N S T A N C E   S I Z E S
    // ######################################################
    ProfileScripts = new Meteor.Collection("profileScripts");

    // Get the list of providers in the system
    Meteor.http.get('http://localhost:8000/api/profile_scripts/', 
        {
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password')
            }
        },
        function (error, response) {
            var i, item, items = response.data;


            // Clear the providers collection
            ProfileScripts.remove({});

            // Insert all providers from the API into the collection
            for (i in items) {
                item = items[i];
                ProfileScripts.insert(item);
            }
        }
    );

});