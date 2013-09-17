define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/security_groups/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var group;

                    deferred.resolve();

                    // Clear the store and the grid
                    stores.SecurityGroup.removeAll();


                    for (i in items) {
                        group = new models.SecurityGroup().create(items[i]);
                        stores.SecurityGroups.push(group);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.log('groups', stores.SecurityGroups());
                    deferred.resolve(stores.SecurityGroups());
                }
            });

            return deferred.promise
        },
        getRules : function (group) {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/security_groups/' + group.id + '/rules/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var rule;

                    deferred.resolve();

                    // Clear the store and the grid
                    stores.SecurityGroupRules.removeAll();

                    // Add rules to the store
                    for (i in items) {
                        rule = new models.SecurityGroupRule().create(items[i]);
                        stores.SecurityGroupRules.push(rule);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.log('groups', stores.SecurityGroupRules());
                    deferred.resolve(stores.SecurityGroupRules());
                }
            });

            return deferred.promise
        }
    }
});