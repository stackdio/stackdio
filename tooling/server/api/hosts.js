Meteor.startup(function () {
    var require = __meteor_bootstrap__.require;


    // ######################################################
    //      H O S T S 
    // ######################################################
    Hosts = new Meteor.Collection("hosts");

    // Get the list of hosts in the system
    Meteor.http.get('http://localhost:8000/api/hosts/', 
        {
            headers: {
                'Accept': 'application/json'
            },
            auth: 'testuser:password'
        },
        function (error, response) {
            var h, host, hosts = JSON.parse(response.content).results;

            // Clear the providers collection
            Hosts.remove({});

            // Insert all providers from the API into the collection
            for (h in hosts) {
                host = hosts[p];
                Hosts.insert(host);
            }
        }
    );

});