if (Meteor.isClient) {
    ProviderAccounts = new Meteor.Collection("provideraccounts");

    Template.accountTable.accounts = function () {
        return ProviderAccounts.find({}).fetch();
    }

    Template.awsAccountForm.rendered = function () {
        console.log(ProviderAccounts.find({}).fetch());
        $('#aws-account-form').validate({
            rules: {
                accountTitle: {
                    minlength: 2,
                    required: true
                },
                accountPurpose: {
                    required: true,
                    minlength: 2
                },
                accessKey: {
                    minlength: 2,
                    required: true
                },
                secretKey: {
                    minlength: 2,
                    required: true
                },
                keypairName: {
                    minlength: 2,
                    required: true
                },
                securityGroups: {
                    minlength: 2,
                    required: true
                }
            },
            highlight: function(element) {
                $(element).closest('.control-group').removeClass('success').addClass('error');
            },
            success: function(element) {
                element
                .text('OK!').addClass('valid')
                .closest('.control-group').removeClass('error').addClass('success');
            }
        });
    }

    Template.accountTable.events({
        'click .aws_account': function (evt, node) {
            console.log(arguments);
        }
    });

    Template.awsAccountForm.events({

        'click #submit-account': function (evt, node) {
            var formData = new FormData(), xhr = new XMLHttpRequest();

            evt.preventDefault();
            evt.stopPropagation();

            // console.log(evt);
            // return;

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

                // Show an animated message containing the result of the upload
                if (evt.target.status === 200 || evt.target.status === 201 || evt.target.status === 302) {
                    ProviderAccounts.insert(JSON.decode(evt.target.responseText));
                } else {
                    console.log(evt);
                    var response = JSON.parse(evt.target.response);

                    for (key in response) {
                        failure = response[key];
                        $('#aws-account-fail').append('<p>' + key + ': ' + failure + '</p>');
                        // $('#awsErrorBody').append('<p>' + key + ': ' + failure + '</p>');
                    }

                    // $('#aws-account-fail').modal('show')
                    $('#aws-account-fail').show();
                }
            };

            // Start the upload process
            xhr.send(formData);
        }
    });
}