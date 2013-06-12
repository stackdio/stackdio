instanceCtrl = function ($scope) {
    $scope.InstanceSizes = InstanceSizes;
    $scope.InstanceSizes = $scope.InstanceSizes.find({}).fetch();
}

accountCtrl = function ($scope) {
    $scope.ProviderAccounts = ProviderAccounts;
    $scope.ProviderAccounts = $scope.ProviderAccounts.find({}).fetch();
}

profileScriptCtrl = function ($scope) {
    $scope.ProfileScripts = ProfileScripts;
    $scope.ProfileScripts = $scope.ProfileScripts.find({}).fetch();
}

profileCtrl = function ($scope) {
    $scope.ProviderProfiles = ProviderProfiles;
    $scope.ProviderProfiles = $scope.ProviderProfiles.find({}).fetch();
}

providerTypeCtrl = function ($scope) {
    $scope.ProviderTypes = ProviderTypes;
    $scope.ProviderTypes = $scope.ProviderTypes.find({}).fetch();
}

roleCtrl = function ($scope) {
    $scope.Roles = Roles;
    $scope.Roles = $scope.Roles.find({}).fetch();
}

stackCtrl = function ($scope) {
    $scope.Stacks = Stacks;
    $scope.Stacks = $scope.Stacks.find({}).fetch();
}
