if (Meteor.isClient) {
    ProviderProfiles = new Meteor.Collection("providerprofiles");

    Template.providerProfileTable.profiles = function () {
        return ProviderProfiles.find({}).fetch();
    }

    Template.providerProfileForm.events({
        'click #submit-profile': function (evt, node) {

            Meteor.http.post('http://localhost:8000/api/profiles/', 
                {
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password')
                    },
                    data: {
                        title: $('#profile-title').val(),
                        description: $('#profile-purpose').val(),
                        cloud_provider: $('#profile-cloud-provider').val(),
                        image_id: $('#profile-image-id').val(),
                        default_instance_size: $('#profile-default-instance-size').val(),
                        script: $('#profile-script').val(),
                        ssh_user: $('#profile-ssh-user').val()
                    }
                },
                function (error, response) {
                    if (response.hasOwnProperty('data')) {
                        ProviderProfiles.insert(response.data);
                    }
                }
            );

        }
    });
}