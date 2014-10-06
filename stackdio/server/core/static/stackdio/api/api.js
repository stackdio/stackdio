define([
        "api/SecurityGroups", 
        "api/Users", 
        "api/Regions",
        "api/InstanceSizes", 
        "api/Profiles", 
        "api/Accounts", 
        "api/ProviderTypes", 
        "api/Snapshots", 
        "api/StackHosts", 
        "api/Formulas", 
        "api/Stacks",
        "api/Search",
        "api/Blueprints"
        ], 
    function (SecurityGroups, Users, Regions, InstanceSizes, Profiles, Accounts, ProviderTypes, Snapshots, StackHosts, Formulas, Stacks, Search, Blueprints) {

    return {
        SecurityGroups: SecurityGroups,
        Users: Users,
        Regions: Regions,
        InstanceSizes: InstanceSizes,
        Profiles:      Profiles,
        Accounts:      Accounts,
        ProviderTypes: ProviderTypes,
        Snapshots:     Snapshots,
        StackHosts:    StackHosts,
        Formulas:      Formulas,
        Stacks:        Stacks,
        Search:        Search,
        Blueprints:    Blueprints
    }
});