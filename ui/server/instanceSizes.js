Meteor.startup(function () {

    // ######################################################
    //      I N S T A N C E   S I Z E S
    // ######################################################
    InstanceSizes = new Meteor.Collection("instanceSizes");

    // Get the list of providers in the system
    Meteor.http.get('http://localhost:8000/api/instance_sizes/', 
        {
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password')
            }
        },
        function (error, response) {
            var i, item, items = JSON.parse(response.content).results;

            // Clear the providers collection
            InstanceSizes.remove({});

            // Insert all providers from the API into the collection
            for (i in items) {
                item = items[i];
                InstanceSizes.insert(item);
            }
        }
    );

});