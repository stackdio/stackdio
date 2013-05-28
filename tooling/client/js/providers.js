if (Meteor.isClient) {
    Providers = new Meteor.Collection("providers");
    // Meteor.subscribe("all-providers");
    Template.providerList.providers = function () {
        return Providers.find({}).fetch();
    }

}

