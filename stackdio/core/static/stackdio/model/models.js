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

    var BlueprintHost = function () {};
    BlueprintHost.prototype = new Model();

    var StackHost = function () {};
    StackHost.prototype = new Model();

    var StackAction = function () {};
    StackAction.prototype = new Model();

    var BlueprintHostVolume = function () {};
    BlueprintHostVolume.prototype = new Model();

    var BlueprintHostAccessRule = function () {};
    BlueprintHostAccessRule.prototype = new Model();

    var Role = function () {};
    Role.prototype = new Model();

    var Formula = function () {};
    Formula.prototype = new Model();

    var FormulaComponent = function () {};
    FormulaComponent.prototype = new Model();

    return {
        SecurityGroup: SecurityGroup,
        AWSSecurityGroup: AWSSecurityGroup,
        SecurityGroupRule: SecurityGroupRule,
        
        ProviderType: ProviderType,
        Account: Account,
        Profile: Profile,
        Zone: Zone,
        InstanceSize: InstanceSize,
        
        Snapshot: Snapshot,
        
        Stack: Stack,
        StackHost: StackHost,
        StackAction: StackAction,

        Blueprint: Blueprint,
        BlueprintHost: BlueprintHost,
        BlueprintHostVolume: BlueprintHostVolume,
        BlueprintHostAccessRule: BlueprintHostAccessRule,
        
        Formula: Formula,
        FormulaComponent: FormulaComponent,
        
        Role: Role
    }
});
