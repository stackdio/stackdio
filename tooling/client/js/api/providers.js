if (Meteor.isClient) {
    Providers = new Meteor.Collection("providers");

    Template.providerTable.providers = function () {
        return Providers.find({}).fetch();
    }
    Template.stackList.providers = function () {
        return Providers.find({}).fetch();
    }
}