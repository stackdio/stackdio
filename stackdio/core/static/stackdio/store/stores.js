define(["knockout"], function (ko) {
    return {
        SecurityGroupRules : ko.observableArray([]),
        AWSSecurityGroups : ko.observableArray([]),
        DefaultSecurityGroups : ko.observableArray([]),
        AccountSecurityGroups : ko.observableArray([]),
        SecurityGroups : ko.observableArray([]),
        Zones : ko.observableArray([]),

        ProviderTypes : ko.observableArray([]),
        Accounts : ko.observableArray([]),
        AccountProfiles : ko.observableArray([]),
        Profiles : ko.observableArray([]),
        
        InstanceSizes : ko.observableArray([]),
        Roles : ko.observableArray([]),
        Snapshots : ko.observableArray([]),
        Formulae : ko.observableArray([]),
        Blueprints : ko.observableArray([]),

        Stacks : ko.observableArray([]),
        StackHosts : ko.observableArray([]),
        
        NewHosts : ko.observableArray([]),
        HostMetadata : ko.observableArray([]),
        HostVolumes : ko.observableArray([]),
        HostAccessRules : ko.observableArray([])
    }
});
