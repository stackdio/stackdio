if (Meteor.isClient) {
    InstanceSizes = new Meteor.Collection("instanceSizes");

    Template.providerProfileForm.instancesizes = function () {
        return InstanceSizes.find({}).fetch();
    }
}