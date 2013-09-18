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
                    stores.SecurityGroups.removeAll();


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
        loadByAccount : function (account) {
            var self = this;
            var deferred = Q.defer();
            var group;

            $.ajax({
                url: '/api/providers/'+account.id+'/security_groups/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var aws = response.provider_groups;

                    // Clear the store and the grid
                    stores.AWSSecurityGroups.removeAll();

                    for (i in aws) {
                        group = new models.AWSSecurityGroup().create(aws[i]);
                        stores.AWSSecurityGroups.push(group);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.log('groups', stores.AWSSecurityGroups());
                    deferred.resolve();
                }
            });

            return deferred.promise
        },
        save : function (group) {
            var self = this;
            var deferred = Q.defer();
            var securityGroup = JSON.stringify(group);


            $.ajax({
                url: '/api/security_groups/',
                type: 'POST',
                data: securityGroup,
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var group;

                    deferred.resolve();

                    // Clear the store and the grid
                    stores.SecurityGroups.removeAll();


                    for (i in items) {
                        group = new models.SecurityGroup().create(items[i]);
                        stores.SecurityGroups.push(group);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.log('security groups', stores.SecurityGroups());
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