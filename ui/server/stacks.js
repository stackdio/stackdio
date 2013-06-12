Meteor.startup(function () {
    var require = __meteor_bootstrap__.require;


    // ######################################################
    //      H O S T S 
    // ######################################################
    Stacks = new Meteor.Collection("stacks");



    // ######################################################
    //      S T A C K S
    // ######################################################
    // Get the list of stacks in the system
    Meteor.http.get('http://localhost:8000/api/stacks/', 
        {
            headers: {
                'Accept': 'application/json'
            },
            auth: 'testuser:password'
        },
        function (error, response) {
            var i, item, items = JSON.parse(response.content).results;

            // Clear the providers collection
            Stacks.remove({});

            // Insert all providers from the API into the collection
            for (i in items) {
                item = items[p];
                Stacks.insert(item);
            }
        }
    );

});