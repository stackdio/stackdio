if (Meteor.isClient) {
    Hosts = new Meteor.Collection("hosts");
    InstanceSizes = new Meteor.Collection("instanceSizes");
    ProfileScripts = new Meteor.Collection("profileScripts");
    ProviderAccounts = new Meteor.Collection("providerAccounts");
    ProviderProfiles = new Meteor.Collection("providerProfiles");
    ProviderTypes = new Meteor.Collection("providerTypes");
    Roles = new Meteor.Collection("roles");
    Stacks = new Meteor.Collection("stacks");
}
