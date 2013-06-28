Ext.define('stackdio.controller.Stack', {
    extend: 'Ext.app.Controller',


    init: function () {
        var me = this;

        me.stackForm = Ext.widget('addStack');


        /*

              ____ ___  _   _ _____ ____   ___  _        _     ___   ____ ___ ____ 
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |      | |   / _ \ / ___|_ _/ ___|
            | |  | | | |  \| | | | | |_) | | | | |      | |  | | | | |  _ | | |    
            | |__| |_| | |\  | | | |  _ <| |_| | |___   | |__| |_| | |_| || | |___ 
             \____\___/|_| \_| |_| |_| \_\\___/|_____|  |_____\___/ \____|___\____|

        */
        me.control({
            '#delete-stack-host': {
                click: function (btn, e) {
                    var host = Ext.getCmp('stack-hosts').getSelectionModel().getSelection()[0];
                    Ext.getStore('StackHosts').remove(host);
                }
            },
            '#stack-hosts': {
                itemcontextmenu: function(view, rec, node, index, e) {
                    e.stopEvent();

                    if (!me.hasOwnProperty('stackHostContextMenu')) {
                        me.stackHostContextMenu = Ext.widget('hostContextMenu');
                    }

                    me.stackHostContextMenu.show();
                    me.stackHostContextMenu.setPagePosition(e.xy);
                    return false;
                }
            },
            '#create-stack-host': {
                click: function (btn, e) {

                }
            },
            '#save-stack-host': {
                click: function (btn, e) {
                    var r, rec, record = me.stackHostForm.down('form').getForm().getValues();

                    record.cloud_profile = me.hostProfileId;

                    Ext.getStore('StackHosts').add({
                        cloud_profile: record.cloud_profile,
                        hostname: record.hostname,
                        roles: record.role[0],
                        security_groups: record.security_groups,
                        count: record.count,
                        instance_size: record.instance_size
                    });

                    btn.up('window').hide();
                }
            },
            '#create-stack': {
                click: function (btn, e) {
                    // When creating a new stack, clear out the store that hold host definitions for stack creation
                    Ext.getStore('StackHosts').removeAll();
                    me.showStackForm();
                }
            },
            '#save-stack': {
                click: function (btn, e) {
                    me.saveStack();
                }
            }

            ,'addStack': {
                boxready: function (widget, w, h, e) {
                    var i, item, items;
                    var store = me.getAccountProfilesStore().data.items;
                    var btn = me.getNewHostButton();

                    for (i in store) {
                        item = store[i];
                        btn.menu.add({
                            text: item.data.title,
                            id: 'profile-' + item.data.id,
                            handler: function () {
                                me.application.fireEvent('stackdio.newhost', this.id.split('-')[1]);
                            }
                        });
                    }

                    var stackKeyMap = new Ext.util.KeyMap(widget.el.dom.id, [
                        {
                            key: 'h',
                            alt: true,
                            fn: function (code, e) {
                                e.preventDefault();
                                me.application.fireEvent('stackdio.newhost', null);
                            },
                            scope: me
                        }
                        ,{
                            key: 13, 
                            alt: false,
                            fn: function (code, e) {
                                e.preventDefault();
                                me.saveStack();
                            },
                            scope: me
                        }
                    ]);

                }
            }

            ,'stackList': {
                itemdblclick : function (grid, item, domEl, evt, eopts, fn) {
                    me.selectedStack = grid.getSelectionModel().getSelection()[0];
                    me.showStackForm(me.selectedStack);
                }
                ,cellclick : function (grid, td, cellIndex, record, tr, rowIndex, e, eOpts) {
                    if (cellIndex === 3) {      // The delete icon


                        Ext.Msg.show({
                            title: 'Are you really sure?',
                            msg:   'You are about to delete a stack. This means all hosts and attached volumes will be terminated as well. Are you really sure about this?',
                            buttons: Ext.Msg.YESNO,
                            icon: Ext.Msg.QUESTION,
                            fn: function (btnId) {
                                if (btnId === 'yes') {
                                    StackdIO.request({
                                        url: record.data.url,
                                        method: 'DELETE',
                                        success: function (response) {
                                            var res = Ext.JSON.decode(response.responseText);
                                            me.application.notification.howl('The stack will now be terminated.', 2000);
                                            Ext.getStore('Stacks').load();
                                        },
                                        failure: function (response) {
                                            me.application.notification.scold('Stack did not save. Update your data and try again.', 3000);
                                        }
                                    });
                                }
                            }
                        });
                    }
                }
            }

            ,'newStackHosts': {
                cellclick : function (grid, td, cellIndex, record, tr, rowIndex, e, eOpts) {
                    if (cellIndex === 6) {      // The delete icon
                        Ext.getStore('StackHosts').remove(record);
                    }
                }
            }

            ,'launchedStackHosts': {
                cellclick : function (grid, td, cellIndex, record, tr, rowIndex, e, eOpts) {
                    if (cellIndex === 4) {      // The delete icon
                        StackdIO.request({
                            url: record.data.url,
                            method: 'DELETE',
                            success: function (response) {
                                var res = Ext.JSON.decode(response.responseText);

                                me.getStackHosts(me.selectedStack.data.hosts);

                                me.application.notification.howl('Host removed.', 2000);
                            },
                            failure: function (response) {
                                me.application.notification.scold('Stack did not save. Update your data and try again.', 3000);
                            }
                        });
                    }
                }
            }


        });


        /*

                 _______     _______ _   _ _____    _   _    _    _   _ ____  _     _____ ____  ____  
                | ____\ \   / / ____| \ | |_   _|  | | | |  / \  | \ | |  _ \| |   | ____|  _ \/ ___| 
                |  _|  \ \ / /|  _| |  \| | | |    | |_| | / _ \ |  \| | | | | |   |  _| | |_) \___ \ 
                | |___  \ V / | |___| |\  | | |    |  _  |/ ___ \| |\  | |_| | |___| |___|  _ < ___) |
                |_____|  \_/  |_____|_| \_| |_|    |_| |_/_/   \_\_| \_|____/|_____|_____|_| \_\____/
        
        */
        /*
         *      Add accounts to the new profile split buttons once store is loaded
         */

        me.application.addListener('stackdio.newhost', function (profileId) {
            var profile;

            if (profileId === null) {
                profile = me.getAccountProfilesStore().getAt(0);
                profileId = profile.data.id;
            } else {
                profile = me.getAccountProfilesStore().findRecord('id', profileId);
            }

            me.hostProfileId = profileId;

            if (!me.hasOwnProperty('stackHostForm')) {
                me.stackHostForm = Ext.widget('addHost');
            }

            me.stackHostForm.show();
            me.stackHostForm.setTitle(profile.data.title + ' host');
            me.stackHostForm.down('combo').setValue(profile.data.default_instance_size);
        });

        me.application.addListener('stackdio.showstacks', function () {
            me.showStackForm();
        });

    },



    /*

              ____ ___  _   _ _____ ____   ___  _     _     _____ ____     _____ _   _ _   _  ____ _____ ___ ___  _   _ ____  
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |   | |   | ____|  _ \   |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___| 
            | |  | | | |  \| | | | | |_) | | | | |   | |   |  _| | |_) |  | |_  | | | |  \| | |     | |  | | | | |  \| \___ \ 
            | |__| |_| | |\  | | | |  _ <| |_| | |___| |___| |___|  _ <   |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
             \____\___/|_| \_| |_| |_| \_\\___/|_____|_____|_____|_| \_\  |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/ 

    */

    saveStack: function () {
        var me = this;
        var r, rec, record = me.stackForm.down('form').getForm().getValues();
        var h, host, hosts = Ext.getStore('StackHosts').data.items;
        var stack = {
            title: record.title,
            description: record.description,
            hosts: []
        };

        for (h in hosts) {
            host = hosts[h];
            stack.hosts.push({
                 host_count: host.data.count
                ,host_size: host.data.instance_size
                ,host_pattern: host.data.hostname
                ,cloud_profile: host.data.cloud_profile
                ,salt_roles: host.data.roles.split(',')
                ,host_security_groups: host.data.security_groups
            });
        }

        console.log(stack);

        StackdIO.request({
            url: '/api/stacks/',
            method: 'POST',
            jsonData: stack,
            success: function (response) {
                var res = Ext.JSON.decode(response.responseText);
                if (res.hasOwnProperty('id')) {
                    // Alert user to success
                    me.application.notification.howl('Stack saved. Will now launch the stack...', 2000);

                    // Clear the store that holds hosts for a new stack
                    Ext.getStore('StackHosts').removeAll();

                    // Clear the stack form by loading an empty record
                    me.stackForm.down('form').getForm().loadRecord(Ext.create('stackdio.model.Stack'));

                    // Hide the stack form
                    me.stackForm.hide();

                    // Reload stack store
                    Ext.getStore('Stacks').load();
                } else {
                    me.application.notification.scold('Stack did not save. Update your data and try again.', 3000);
                }
            },
            failure: function (response) {
                me.application.notification.scold('Stack did not save. Update your data and try again.', 3000);
            }
        });

    }
   
    ,showStackForm: function (record) {
        var me = this;
        var accounts = me.getProviderAccountsStore();
        var profiles = me.getAccountProfilesStore();

        // Check if there are accounts and profiles before showing stack form
        if (accounts.data.length === 0) {
            Ext.Msg.show({
                title: 'Setup incomplete',
                msg:   'There are no provider accounts set up yet. Would you like to create one now?',
                buttons: Ext.Msg.YESNO,
                icon: Ext.Msg.QUESTION,
                fn: function (btnId) {
                    if (btnId === 'yes') {
                        me.application.fireEvent('stackdio.showaccounts');
                        me.application.fireEvent('stackdio.newaccount', null);
                    }
                }
            });

            return;
        }

        if (profiles.data.length === 0) {
            Ext.Msg.show({
                title: 'Setup incomplete',
                msg:   'There are no provider profiles set up yet. Would you like to create one now?',
                buttons: Ext.Msg.YESNO,
                icon: Ext.Msg.QUESTION,
                fn: function (btnId) {
                    if (btnId === 'yes') {
                        me.application.fireEvent('stackdio.newprofile', null);
                        me.application.fireEvent('stackdio.showprofiles');
                    }
                }
            });

            return;
        }

        if (!me.hasOwnProperty('stackForm')) {
            me.stackForm = Ext.widget('addStack');
        }

        me.stackForm.show();

        if (typeof record !== 'undefined') {
            me.stackForm.down('form').getForm().loadRecord(record);
            me.stackForm.down('launchedStackHosts').show();
            me.stackForm.down('newStackHosts').hide();

            me.getStackHosts(record.data.hosts);
        } else {
            me.stackForm.down('form').getForm().loadRecord(Ext.create('stackdio.model.Stack'));
            me.stackForm.down('launchedStackHosts').hide();
            me.stackForm.down('newStackHosts').show();
        }

    }

    ,getStackHosts: function (hostUrl) {
        var me = this;

        StackdIO.request({
            url: hostUrl,
            method: 'GET',
            success: function (response) {
                var res = Ext.JSON.decode(response.responseText);
                var i, item, items = res.results;
                var store = me.getLaunchedHostsStore();

                store.removeAll();

                for (i in items) {
                    item = items[i];
                    store.add(item);
                }
            },
            failure: function (response) {
                me.application.notification.scold('Error retrieving list of hosts for your stack.', 3000);
            }
        });
    }



    /*

             ____    ___   _   _   ____    ___   _   _    ____   ____  
            | __ )  |_ _| | \ | | |  _ \  |_ _| | \ | |  / ___| / ___| 
            |  _ \   | |  |  \| | | | | |  | |  |  \| | | |  _  \___ \ 
            | |_) |  | |  | |\  | | |_| |  | |  | |\  | | |_| |  ___) |
            |____/  |___| |_| \_| |____/  |___| |_| \_|  \____| |____/ 


    */
    ,views: [
         'stack.List'
        ,'stack.Add'
        ,'stack.HostContextMenu'
        ,'host.Add'
        ,'stack.NewHosts'
        ,'stack.LaunchedHosts'
        ,'volume.HostVolumeList'
    ]

    ,models: [
         'Stack'
        ,'StackHost'
    ]

    ,stores: [
         'StackHosts'
        ,'Stacks'
        ,'AccountProfiles'
        ,'LaunchedHosts'
        ,'InstanceSizes'
        ,'Roles'
        ,'ProviderAccounts'
    ],


    /*

             ____    _____   _____   _____   ____    _____   _   _    ____   _____   ____  
            |  _ \  | ____| |  ___| | ____| |  _ \  | ____| | \ | |  / ___| | ____| / ___| 
            | |_) | |  _|   | |_    |  _|   | |_) | |  _|   |  \| | | |     |  _|   \___ \ 
            |  _ <  | |___  |  _|   | |___  |  _ <  | |___  | |\  | | |___  | |___   ___) |
            |_| \_\ |_____| |_|     |_____| |_| \_\ |_____| |_| \_|  \____| |_____| |____/ 

    */
    refs: [
        {
            ref: 'newHostButton', selector: '#create-stack-host'
        }
    ]
});


