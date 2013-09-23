define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        get : function (group) {
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
                    stores.DefaultSecurityGroups.removeAll();

                    for (i in aws) {
                        group = new models.AWSSecurityGroup().create(aws[i]);
                        stores.AWSSecurityGroups.push(group);
                    }

                    for (i in items) {
                        group = new models.SecurityGroup().create(items[i]);

                        if (items[i].is_default) {
                            stores.DefaultSecurityGroups.push(group);
                        } else {
                            stores.SecurityGroups.push(group);
                        }
                    }

                    var flattened = stores.AWSSecurityGroups().map(function (g) {
                        return g.name;
                    });

                    $('#new_securitygroup_name').typeahead({
                        source: flattened,
                        items: 10,
                        minLength: 2
                    });

                    // Resolve the promise and pass back the loaded items
                    console.log('account groups', stores.SecurityGroups());
                    console.log('default groups', stores.DefaultSecurityGroups());
                    deferred.resolve();
                }
            });

            return deferred.promise
        },
        saveDefault : function (group) {
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
                    var item = response;
                    var newGroup = new models.SecurityGroup().create(item);

                    console.log('saved group as default');
                    stores.DefaultSecurityGroups.push(newGroup);
                    console.log('default groups', stores.DefaultSecurityGroups());
                    deferred.resolve(group);
                },
                error: function (request, status, error) {
                    var newGroup = new models.SecurityGroup().create(group);

                    if (error === 'CONFLICT') {
                        console.log('group already exists, so setting to default');
                        group.is_default = true;

                        console.log(securityGroup);

                        self.updateDefault(securityGroup)
                            .then(function () {
                                deferred.resolve();
                            });

                    } else {
                        deferred.reject(new Error(error));
                    }
                }
            });

            return deferred.promise
        },
        updateDefault : function (group) {
            var self = this;
            var deferred = Q.defer();
            var securityGroup = JSON.stringify(group);


            $.ajax({
                url: '/api/security_groups/' + group.id + '/',
                type: 'PUT',
                data: securityGroup,
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    var group = response;

                    if (!group.is_default) {
                        stores.DefaultSecurityGroups.remove(function (g) {
                            return g.id === group.id;
                        });
                    }

                    deferred.resolve(group);
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