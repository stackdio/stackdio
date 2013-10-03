define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        load : function (pageURL) {
            var self = this;
            var deferred = Q.defer();
            var url = pageURL || '/api/security_groups/';

            $.ajax({
                url: url,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var count = response.count, next = response.next, previous = response.previous;
                    var group;

                    // Clear the store and the grid
                    stores.SecurityGroups.removeAll();

                    for (i in items) {
                        group = new models.SecurityGroup().create(items[i]);

                        // The owner property is only provided if the user is a superuser.
                        if (!stackdio.settings.superuser) group.owner = '';

                        // Attach the corresponding Account to the group
                        group.account = _.find(stores.Accounts(), function (a) {
                            return a.id === group.provider_id;
                        });

                        // Add to store
                        stores.SecurityGroups.push(group);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.info('groups', stores.SecurityGroups());
                    deferred.resolve({count: count, next: next, previous: previous});
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

                    // All AWS groups are returned in the 'provider_groups' key on the response
                    for (i in aws) {
                        group = new models.AWSSecurityGroup().create(aws[i]);
                        stores.AWSSecurityGroups.push(group);
                    }

                    // All stackd.io groups are returned in the 'results' key on the response
                    for (i in items) {
                        group = new models.SecurityGroup().create(items[i]);

                        if (items[i].is_default) {
                            stores.DefaultSecurityGroups.push(group);
                        }
                        stores.AccountSecurityGroups.push(group);
                    }

                    // Extract the name of each group into a new array that is used as the 
                    // store for the typeahead field on the default group form
                    var flattened = stores.AWSSecurityGroups().map(function (g) {
                        return g.name;
                    });

                    $('#new_securitygroup_name').typeahead({
                        source: flattened,
                        items: 10,
                        minLength: 2
                    });

                    // Resolve the promise and pass back the loaded items
                    console.log('account groups', stores.AccountSecurityGroups());
                    console.log('default groups', stores.DefaultSecurityGroups());
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
                    var item = response;
                    var newGroup = new models.SecurityGroup().create(item);

                    // The owner property is only provided if the user is a superuser.
                    if (!stackdio.settings.superuser) newGroup.owner = '';


                    stores.DefaultSecurityGroups.push(newGroup);
                    deferred.resolve(newGroup);
                },
                error: function (request, status, error) {
                    if (error === 'CONFLICT') {
                        var newGroup = _.findWhere(stores.AccountSecurityGroups(), { name: group.name });

                        if (typeof newGroup !== "undefined") {
                            console.log('group already exists, so setting to default');
                            newGroup.is_default = true;


                            self.updateDefault(newGroup)
                                .then(function () {
                                    deferred.resolve();
                                });
                            
                        } else {
                            deferred.resolve();
                        }
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
                    } else {
                        stores.DefaultSecurityGroups.push(group);
                    }

                    deferred.resolve(group);
                }
            });

            return deferred.promise
        },
        delete : function (group) {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/security_groups/' + group.id + '/',
                type: 'DELETE',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    // Remove the Security Group from the local array
                    stores.SecurityGroups.remove(function (g) {
                        return g.id === group.id;
                    });

                    // Resolve the promise
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    console.log(arguments);

                    deferred.reject(new Error(JSON.parse(request.responseText).detail));
                }
            });

            return deferred.promise
        },
        updateRule : function (group, rule, action) {
            var self = this;
            var deferred = Q.defer();
            var stringifiedRule = JSON.stringify(rule);

            $.ajax({
                url: '/api/security_groups/' + group.id + '/rules/',
                data: stringifiedRule,
                type: 'PUT',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    // Replace the rules array on the current group
                    group.rules = response;

                    // Empty the rules store
                    stores.SecurityGroupRules.removeAll();

                    // Push the new rules back into the store
                    _.each(response, function (r) {
                        stores.SecurityGroupRules.push(r);
                    })

                    // Resolve the promise
                    deferred.resolve();
                }
            });

            return deferred.promise
        }
    }
});