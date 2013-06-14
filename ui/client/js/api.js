if (Meteor.isClient) {
    Hosts               = new Meteor.Collection("hosts");
    Roles               = new Meteor.Collection("roles");
    Stacks              = new Meteor.Collection("stacks");
    InstanceSizes       = new Meteor.Collection("instanceSizes");
    ProviderTypes       = new Meteor.Collection("providerTypes");
    ProfileScripts      = new Meteor.Collection("profileScripts");
    ProviderAccounts    = new Meteor.Collection("providerAccounts");
    ProviderProfiles    = new Meteor.Collection("providerProfiles");
}
