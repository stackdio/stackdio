(function(){ 
    var app;

    angular.element(document).ready(function() {
        return angular.bootstrap(document, ['app']);
    });

    app = angular.module('app', ['ngMeteor'], [
        '$routeProvider', 
        '$locationProvider',
        function($routeProvider, $locationProvider) {
            $routeProvider.when('/', {
                templateUrl: 'welcome.blade'
            }).when('/dashboard', {
                templateUrl: 'dashboard.blade'
            }).when('/accounts', {
                templateUrl: 'accounts.blade'
            }).when('/profiles', {
                templateUrl: 'profiles.blade'
            }).when('/stacks', {
                templateUrl: 'stacks.blade'
            }).when('/blueprints', {
                templateUrl: 'blueprints.blade'
            }).when('/schedules', {
                templateUrl: 'schedules.blade'
            }).when('/roles', {
                templateUrl: 'roles.blade'
            });

            return $locationProvider.html5Mode(true);
        }
    ]);

    angular.module('directives', []).directive('opendialog',
        function () {
            var openDialog = {
                link : function (scope, element, attrs) {
                    function openDialog() {
                        var element = angular.element('#account-form');
                        var ctrl = element.controller();
                        ctrl.setModel(scope.blub);
                        element.modal('show');
                    }
                    element.bind('click', openDialog);
                }
            }
            return openDialog;
        }
    );

}).call(this);
