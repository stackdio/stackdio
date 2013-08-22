define(["knockout"], function (ko) {
    return {
        ProviderTypes : ko.observableArray([]),
        Accounts : ko.observableArray([]),
        Profiles : ko.observableArray([]),
        NewHosts : ko.observableArray([]),
        HostVolumes : ko.observableArray([]),
        InstanceSizes : ko.observableArray([]),
        Roles : ko.observableArray([]),
        Snapshots : ko.observableArray([]),
        Stacks : ko.observableArray([])
    }
});

// require(["lib/knockout"], function (ko) {
//     stackdio.stores.ProviderTypes = ko.observableArray([]);
//     stackdio.stores.Accounts = ko.observableArray([]);
//     stackdio.stores.Profiles = ko.observableArray([]);
//     stackdio.stores.NewHosts = ko.observableArray([]);
//     stackdio.stores.HostVolumes = ko.observableArray([]);
//     stackdio.stores.InstanceSizes = ko.observableArray([]);
//     stackdio.stores.Roles = ko.observableArray([]);
//     stackdio.stores.Snapshots = ko.observableArray([]);
//     stackdio.stores.Stacks = ko.observableArray([]);