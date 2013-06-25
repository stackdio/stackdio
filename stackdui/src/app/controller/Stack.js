Ext.define('stackdio.controller.Stack', {
    extend: 'Ext.app.Controller',


    init: function () {
        var me = this;


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
                        url: 'http://localhost:8000/api/stacks/',
                        method: 'POST',
                        jsonData: stack,
                        success: function (response) {
                            var res = Ext.JSON.decode(response.responseText);
                            if (res.hasOwnProperty('id')) {
                                me.application.notification.howl('Stack saved. Will now launch the stack...', 2000);

                                btn.up('window').destroy();
                                me.stackHostForm.down('form').getForm().reset();

                                Ext.getStore('StackHosts').removeAll();
                            } else {
                                me.application.notification.scold('Stack did not save. Update your data and try again.', 3000);
                            }
                        },
                        failure: function (response) {
                            me.application.notification.scold('Stack did not save. Update your data and try again.', 3000);
                        }
                    });
                }
            },

            'addStack': {
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
            me.hostProfileId = profileId;

            if (!me.hasOwnProperty('stackHostForm')) {
                me.stackHostForm = Ext.widget('addHost');
            }

            me.stackHostForm.show();

        });
       
    },



    /*

              ____ ___  _   _ _____ ____   ___  _     _     _____ ____     _____ _   _ _   _  ____ _____ ___ ___  _   _ ____  
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |   | |   | ____|  _ \   |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___| 
            | |  | | | |  \| | | | | |_) | | | | |   | |   |  _| | |_) |  | |_  | | | |  \| | |     | |  | | | | |  \| \___ \ 
            | |__| |_| | |\  | | | |  _ <| |_| | |___| |___| |___|  _ <   |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
             \____\___/|_| \_| |_| |_| \_\\___/|_____|_____|_____|_| \_\  |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/ 

    */
   
    showStackForm: function (record) {
        var me = this; 

        if (!me.hasOwnProperty('stackForm')) {
            me.stackForm = Ext.widget('addStack');
        }

        me.stackForm.show();

        if (typeof record !== 'undefined') {
            me.stackForm.down('form').getForm().loadRecord(record);
        }
    },



    /*

             ____    ___   _   _   ____    ___   _   _    ____   ____  
            | __ )  |_ _| | \ | | |  _ \  |_ _| | \ | |  / ___| / ___| 
            |  _ \   | |  |  \| | | | | |  | |  |  \| | | |  _  \___ \ 
            | |_) |  | |  | |\  | | |_| |  | |  | |\  | | |_| |  ___) |
            |____/  |___| |_| \_| |____/  |___| |_| \_|  \____| |____/ 


    */
    views: [
         'stack.List'
        ,'stack.Add'
        ,'stack.HostContextMenu'
        ,'host.Add'
    ],

    models: [
        'Stack'
    ],

    stores: [
         'StackHosts'
        ,'Stacks'
        ,'AccountProfiles'
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


