Meteor.startup(function () {

    // ######################################################
    //      P R O V I D E R   A C C O U N T S
    // ######################################################
    ProviderAccounts = new Meteor.Collection("provideraccounts");

    // Get the list of ProviderAccounts in the system
    Meteor.http.get('http://localhost:8000/api/providers/', 
        {
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password')
            }
        },
        function (error, response) {
            var i, item, items = response.data.results;
            
            // Clear the ProviderAccounts collection
            ProviderAccounts.remove({});

            // Insert all ProviderAccounts from the API into the collection
            for (i in items) {
                item = items[i];
                ProviderAccounts.insert(item);
            }

            // Publish the Accounts in the all-Accounts channel
            // Meteor.publish("all-Accounts", function () {
            //     return Accounts.find(); // everything
            // });

        }
    );

});