define([
        "api/SecurityGroups", 
        "api/Users", 
        "api/Zones", 
        "api/InstanceSizes", 
        "api/Profiles", 
        "api/Accounts", 
        "api/ProviderTypes", 
        "api/Snapshots", 
        "api/StackHosts", 
        "api/Formulae", 
        "api/Stacks",
        "api/Blueprints"
        ], 
    function (SecurityGroups, Users, Zones, InstanceSizes, Profiles, Accounts, ProviderTypes, Snapshots, StackHosts, Formulae, Stacks, Blueprints) {

    return {
        SecurityGroups: SecurityGroups,
        Users: Users,
        Zones: Zones,
        InstanceSizes: InstanceSizes,
        Profiles:      Profiles,
        Accounts:      Accounts,
        ProviderTypes: ProviderTypes,
        Snapshots:     Snapshots,
        StackHosts:    StackHosts,
        Formulae:      Formulae,
        Stacks:        Stacks,
        Blueprints:    Blueprints
    }
});