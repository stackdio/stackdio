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

}).call(this);
