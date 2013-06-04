if (Meteor.isClient) {
    ProviderTypes = new Meteor.Collection("providertypes");

    Template.accountList.providertypes = function () {
        return ProviderTypes.find({}).fetch();
    }
}