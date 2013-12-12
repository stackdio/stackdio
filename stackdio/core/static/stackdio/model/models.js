define(function () {

    var Model = function () {};
    Model.prototype.create = function (record) {
        var self = this;
        for (k in record) { self[k] = record[k]; }
        return self;
    };

    var AWSSecurityGroup = function () {};
    AWSSecurityGroup.prototype = new Model();

    var SecurityGroup = function () {};
    SecurityGroup.prototype = new Model();

    var SecurityGroupRule = function () {};
    SecurityGroupRule.prototype = new Model();

    var Zone = function () {};
    Zone.prototype = new Model();

    var Stack = function () {};
    Stack.prototype = new Model();

    var ProviderType = function () {};
    ProviderType.prototype = new Model();

    var Account = function () {};
    Account.prototype = new Model();

    var Profile = function () {};
    Profile.prototype = new Model();

    var Blueprint = function () {};
    Blueprint.prototype = new Model();

    var InstanceSize = function () {};
    InstanceSize.prototype = new Model();

    var Snapshot = function () {};
    Snapshot.prototype = new Model();

    var NewHost = function () {};
    NewHost.prototype = new Model();

    var StackHost = function () {};
    StackHost.prototype = new Model();

    var NewHostVolume = function () {};
    NewHostVolume.prototype = new Model();

    var Role = function () {};
    Role.prototype = new Model();

    var Formula = function () {};
    Formula.prototype = new Model();

    return {
        SecurityGroupRule: SecurityGroupRule,
        AWSSecurityGroup: AWSSecurityGroup,
        SecurityGroup: SecurityGroup,
        Zone: Zone,
        Stack: Stack,
        StackHost: StackHost,
        ProviderType: ProviderType,
        Account: Account,
        Profile: Profile,
        InstanceSize: InstanceSize,
        Snapshot: Snapshot,
        NewHost: NewHost,
        NewHostVolume: NewHostVolume,
        Formula: Formula,
        Blueprint: Blueprint,
        Role: Role
    }
});