if (Meteor.isClient) {
    ProviderAccounts = new Meteor.Collection("provideraccounts");

    Template.accountTable.accounts = function () {
        return ProviderAccounts.find({}).fetch();
    }

    Template.awsAccountForm.events({
        'click #submit-account': function (evt, node) {
            var formData = new FormData(), xhr = new XMLHttpRequest();

            // A reference to the files selected
            files = evt.target.form[7].files;

            // Append each file to the FormData() object
            for (var i = 0; i < files.length; i++) {
                formData.append('private_key_file', files[i]);
            }

            // Append all other required fields to the form data
            formData.append('provider_type', $('#provider-type').val());
            formData.append('title', $('#account-title').val());
            formData.append('description', $('#account-purpose').val());
            formData.append('access_key_id', $('#aws-access-key').val());
            formData.append('secret_access_key', $('#aws-secret-key').val());
            formData.append('keypair', $('#aws-keypair-name').val());
            formData.append('security_groups', $('#aws-security-groups').val());

            // Open the connection to the provider URI and set authorization header
            xhr.open('POST', 'http://localhost:8000/api/providers/');
            xhr.setRequestHeader('Authorization', 'Basic ' + Base64.encode('testuser:password'));


            // Define any actions to take once the upload is complete
            xhr.onloadend = function (evt) {
                var response_data;

                console.log(evt);
                return;

                // Show an animated message containing the result of the upload
                if (evt.target.status === 200 || evt.target.status === 302) {
                    response_data = JSON.decode(evt.target.responseText);
                } else {
                    console.log(evt);
                }
            };

            // Start the upload process
            xhr.send(formData);


            // Meteor.http.post('http://localhost:8000/api/providers/', 
            //     {
            //         headers: {
            //             "Authorization": "Basic " + Base64.encode('testuser:password')
            //         },
            //         data: {
            //             title: $('#profile-title').val(),
            //             description: $('#profile-purpose').val(),
            //             cloud_provider: $('#profile-cloud-provider').val(),
            //             image_id: $('#profile-image-id').val(),
            //             default_instance_size: $('#profile-default-instance-size').val(),
            //             script: $('#profile-script').val(),
            //             ssh_user: $('#profile-ssh-user').val()
            //         }
            //     },
            //     function (error, response) {
            //         if (response.hasOwnProperty('data')) {
            //             ProviderProfiles.insert(response.data);
            //         }
            //     }
            // );

        }
    });
}