define([
        "app/api/SecurityGroups", 
        "app/api/Users", 
        "app/api/Zones", 
        "app/api/InstanceSizes", 
        "app/api/Profiles", 
        "app/api/Accounts", 
        "app/api/ProviderTypes", 
        "app/api/Roles", 
        "app/api/Snapshots", 
        "app/api/StackHosts", 
        "app/api/Formulae", 
        "app/api/Stacks"
        ], 
    function (SecurityGroups, Users, Zones, InstanceSizes, Profiles, Accounts, ProviderTypes, Roles, Snapshots, StackHosts, Formulae, Stacks) {

    return {
        SecurityGroups: SecurityGroups,
        Users: Users,
        Zones: Zones,
        InstanceSizes: InstanceSizes,
        Profiles:      Profiles,
        Accounts:      Accounts,
        ProviderTypes: ProviderTypes,
        Roles:         Roles,
        Snapshots:     Snapshots,
        StackHosts:    StackHosts,
        Formulae:      Formulae,
        Stacks:        Stacks
    }
});