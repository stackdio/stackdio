if (Meteor.isClient) {
    ProfileScripts = new Meteor.Collection("profileScripts");

    Template.providerProfileForm.profileScripts = function () {
        return ProfileScripts.find({}).fetch();
    }
}