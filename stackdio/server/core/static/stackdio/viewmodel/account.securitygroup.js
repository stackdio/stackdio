define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/AccountSecurityGroups',
    'api/api'
],
function (Q, ko, $galaxy, alerts, formutils, ProviderTypeStore, AccountStore, ProfileStore, AccountSecurityGroupStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedAccount = ko.observable(null);
        self.selectedProviderType = ko.observable(null);
        self.accountTitle = ko.observable(null);
        self.saveAction = self.createAccount;
        self.DefaultGroupStore = ko.observableArray();
        self.stackdioGroupStore = ko.observableArray();
        self.$galaxy = $galaxy;

        self.accountGroupSearchText = ko.observable("");
        self.stackdioGroupSearchText = ko.observable("");

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.AccountSecurityGroupStore = AccountSecurityGroupStore;


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'account.securitygroup';
        self.templatePath = 'securityGroups.html';
        self.domBindingId = '#account-securitygroup';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            ProviderTypeStore.populate().then(function () {
                return AccountStore.populate();
            }).then(function () {
                return ProfileStore.populate();
            }).then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var account = null;
            var provider_type = null;


            if (data.hasOwnProperty('account')) {
                account = AccountStore.collection().filter(function (a) {
                    return a.id === parseInt(data.account, 10);
                })[0];

                self.accountTitle(account.title);
                self.selectedAccount(account);

                API.SecurityGroups.loadByAccount(account).then(function (data) {
                    self.AccountSecurityGroupStore.empty();
                    for (var group in data.provider_groups) {
                        var thisGroup = data.provider_groups[group];
                        thisGroup.display_name = thisGroup.name + ' (' + thisGroup.group_id + ') ' + thisGroup.description;
                        self.AccountSecurityGroupStore.add(thisGroup);
                    }

                    self.AccountSecurityGroupStore.collection.sort(compareGroups);

                    self.stackdioGroupStore.removeAll();
                    self.DefaultGroupStore.removeAll();
                    data.results.forEach(function (group) {
                        group.display_name = group.name + ' (' + group.description + ')';

                        if (!group.is_managed) {
                            self.stackdioGroupStore.push(group);
                        }

                        if (group.is_default) {
                            self.DefaultGroupStore.push(group);
                        }
                    });

                    self.stackdioGroupStore.sort(compareGroups);
                    self.DefaultGroupStore.sort(compareGroups);

                    self.listDefaultGroups();
                }).catch(function (error) {
                    alerts.showMessage('#error', 'Unable to load security groups for this provider. ' + error.message, false);
                });
            }
        };

        function compareGroups(left, right) {
            var leftLower = left.name.toLowerCase();
            var rightLower = right.name.toLowerCase();
            if (leftLower < rightLower)
                return -1;
            if (leftLower > rightLower)
                return 1;
            return 0;
        }

        self.accountGroups = function () {
            return self.AccountSecurityGroupStore.collection().filter(function (ref) {
                return ref.name.indexOf(self.accountGroupSearchText()) > -1;
            });
        };

        self.stackdioGroups = function () {
            return self.stackdioGroupStore().filter(function (ref) {
                return ref.name.indexOf(self.stackdioGroupSearchText()) > -1;
            });
        };

        self.cancelChanges = function (model, evt) {
            $galaxy.transport('account.list');
        };

        self.capture = function (model, evt) {
            if (evt.charCode === 13) {
                self.addNewDefaultSecurityGroup();
                return false;
            }
            return true;
        };

        self.captureNewGroup = function (model, evt) {
            if (evt.charCode === 13) {
                self.addSecurityGroup(document.getElementById('securitygroup_name').value);
                return false;
            }
            return true;
        };

        self.addNewDefaultSecurityGroup = function (model, evt) {
            var record = {};
            record.name = document.getElementById('new_securitygroup_name').value;
            record.cloud_provider = self.selectedAccount().id;
            record.is_default = true;
            record.description = "";

            API.SecurityGroups.save(record).then(function (newGroup) {
                self.DefaultGroupStore.push(newGroup);
                self.resetView();
            })
            .catch(function (error) {
                console.error(error);
            }).done();
        };

        self.addAWSDefaultSecurityGroup = function (model, evt) {
            var selectedId = document.getElementById('aws_security_group').value;

            var selectedGroup = self.AccountSecurityGroupStore.collection().filter(function (group) {
                return group.group_id === selectedId;
            })[0];

            var record = {};
            record.group_id = selectedGroup.group_id;
            record.name = selectedGroup.name;
            record.cloud_provider = self.selectedAccount().id;
            record.is_default = true;
            record.description = "";

            API.SecurityGroups.save(record).then(function (newGroup) {
                self.DefaultGroupStore.push(newGroup);
                self.resetView();
                self.accountGroupSearchText("");
            })
            .catch(function (error) {
                console.error(error);
            }).done();
        };


        self.addStackdioDefaultSecurityGroup = function (model, evt) {
            var selectedId = document.getElementById('stackdio_security_group').value;

            var selectedGroup = self.stackdioGroupStore().filter(function (group) {
                return group.id === parseInt(selectedId, 10);
            })[0];
            console.log('selectedGroup',selectedGroup);
                
            if (self.DefaultGroupStore().indexOf(selectedGroup) > -1) {
                console.log("Group already selected");
                return;
            }

            var record = {};
            record.name = selectedGroup.name;
            record.group_id = selectedGroup.group_id;
            record.cloud_provider = self.selectedAccount().id;
            record.is_default = true;
            record.description = "";
            record.url = selectedGroup.url;

            API.SecurityGroups.updateDefault(record).then(function (newGroup) {
                self.DefaultGroupStore.push(newGroup);
                self.resetView();
                self.stackdioGroupSearchText("");
            })
            .catch(function (error) {
                if (error.message === 'CONFLICT') {
                    API.SecurityGroups.updateDefault(record).then(function (newGroup) {
                        self.DefaultGroupStore.push(newGroup);
                        self.resetView();
                    }).catch(function (error) {
                        alerts.showMessage('#error', 'Unable to add security group as a default. Please try again.', true);
                    }).done();
                }

            }).done();
        };

        self.resetView = function () {
            $('#new_securitygroup_name').val('');
            $('#stackdio_security_group').attr('selectedIndex', '-1').find("option:selected").removeAttr("selected");
            $('#aws_security_group').attr('selectedIndex', '-1').find("option:selected").removeAttr("selected");
            self.listDefaultGroups();
            self.init({account: self.selectedAccount().id});
        };

        self.deleteDefaultSecurityGroup = function (groupId) {
            var record = _.findWhere(self.DefaultGroupStore(), { id: parseInt(groupId, 10) });

            if (typeof record !== 'undefined') {
                record.is_default = false;

                API.SecurityGroups.updateDefault(record).then(function () {
                    self.listDefaultGroups();
                })
                .catch(function (error) {
                    record.is_default = true;
                    console.error(error);
                }).done();
            }
        };

        self.listDefaultGroups = function () {
            var account = self.selectedAccount();

            $('#default_group_list').empty();

            // For each security group that is default, add a label styled span element in the UI
            _.each(self.DefaultGroupStore(), function (g) {
                if (g.is_default && g.provider_id === account.id) {
                    $('#default_group_list').append('<span id="defaultgroup_'+ g.id +'" style="cursor: pointer; margin: 0 5px;" defaultlabel class="label label-success"><span class="iconic-x"></span> '+ g.name +'</span>');
                }
            });

            // Handle the user clicking on the group label to set the group to is_default:false
            $('span[defaultlabel]').click(function (evt) {
                var groupId = evt.target.id.split('_')[1];
                self.deleteDefaultSecurityGroup(groupId);
            });
        };

        self.setForAccount = function (account) {
            if (!account.hasOwnProperty('security_group') || !account.hasOwnProperty('yaml')) {
                var accountsLength = stores.Accounts().length;
                var account = stores.Accounts()[accountsLength - 1];
            }
            self.selectedAccount(account);

            API.SecurityGroups.loadByAccount(account)
                .then(function () {
                    $('#stackdio_security_group').selectpicker();
                    
                    self.listDefaultGroups();
                });
            self.showDefaultGroupForm();
        };
    };
    return new vm();
});
