Ext.define('stackdio.controller.Application', {
    extend: 'Ext.app.Controller',


    init: function () {
        var me = this;

        me.application.notification = Ext.widget('howler', { parentEl: 'title-panel' });


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
                    if (!me.hasOwnProperty('stackHostForm')) {
                        me.stackHostForm = Ext.widget('addHost');
                    }

                    me.stackHostForm.show();
                }
            },
            '#save-stack-host': {
                click: function (btn, e) {
                    var r, rec, record = me.stackHostForm.down('form').getForm().getValues();

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
                    me.showStackForm();
                }
            },
            '#save-stack': {
                click: function (btn, e) {
                    var r, rec, record = me.stackForm.down('form').getForm().getValues();
                    var h, host, hosts = Ext.getStore('Hosts').data.items;
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

                    console.log(record);
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
            '#create-profile': {
                click: function (btn, e) {
                    me.showProfileForm();
                }
            },
            '#save-profile': {
                click: function (btn, e) {
                    var verb, urlSuffix = '', r, rec, record = me.profileForm.down('form').getForm().getValues();

                    if (record.hasOwnProperty('id')) {
                        verb = 'PUT';
                        urlSuffix = me.selectedProfile.data.id + '/';
                    } else {
                        verb = 'POST';
                    }

                    StackdIO.request({
                        url: 'http://localhost:8000/api/profiles/' + urlSuffix,
                        method: verb,
                        jsonData: record,
                        success: function (response) {
                            var res = Ext.JSON.decode(response.responseText);
                            if (res.hasOwnProperty('id')) {
                                me.application.notification.howl('Profile saved...', 2000);
                                btn.up('window').hide();
                                Ext.getStore('AccountProfiles').load();
                            } else {
                                me.application.notification.scold('Profile did not save. Update your data and try again', 3000);
                            }
                        },
                        failure: function (response) {
                            me.application.notification.scold('Profile did not save. Update your data and try again', 3000);
                        }
                    });
                }
            },
            '#create-account': {
                click: function (btn, e) {
                    me.showAccountForm();
                }
            },
            '#save-account': {
                click: function (btn, e) {
                    var r, rec, record = me.accountForm.down('form').getForm().getValues();
                    var formData = new FormData(), xhr = new XMLHttpRequest();

                    e.preventDefault();
                    e.stopPropagation();

                    // A reference to the files selected
                    files = me.accountForm.down('filefield').fileInputEl.dom.files;

                    // Append each file to the FormData() object
                    for (var i = 0; i < files.length; i++) {
                        formData.append('private_key_file', files[i]);
                    }

                    // Append all other required fields to the form data
                    for (r in record) {
                        rec = record[r];
                        formData.append(r, rec);
                        
                    }

                    // Open the connection to the provider URI and set authorization header
                    xhr.open('POST', 'http://localhost:8000/api/providers/');
                    xhr.setRequestHeader('Authorization', 'Basic ' + Base64.encode('testuser:password'));

                    // Define any actions to take once the upload is complete
                    xhr.onloadend = function (evt) {
                        var response_data;

                        // Show an animated message containing the result of the upload
                        if (evt.target.status === 200 || evt.target.status === 201 || evt.target.status === 302) {
                            me.application.notification.howl('New account saved.', 1000);
                        } else {
                            console.log(evt);
                            var html=[], response = JSON.parse(evt.target.response);

                            for (key in response) {
                                failure = response[key];
                                html.push('<p>' + key + ': ' + failure + '</p>');
                            }
                            me.application.notification.scold('New account failed to save. Check your data and try again...'+html, 5000);
                        }
                    };

                    // Start the upload process
                    xhr.send(formData);

                }
            },
            'profileList': {
                itemdblclick : function (grid, item, domEl, evt, eopts, fn) {
                    me.selectedProfile = grid.getSelectionModel().getSelection()[0];
                    me.showProfileForm(me.selectedProfile);
                }
            },
            'accountList': {
                itemdblclick : function (grid, item, domEl, evt, eopts, fn) {
                    me.selectedAccount = grid.getSelectionModel().getSelection()[0];
                    me.showAccountForm(me.selectedAccount);
                }
            },




            '#accounts-button': {
                click: function (btn, e) {
                    Ext.getCmp('content-area').getLayout().setActiveItem(1);
                }
            },

            '#dashboard-button': {
                click: function (btn, e) {
                    Ext.getCmp('content-area').getLayout().setActiveItem(0);
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
         *      Handle the base search for entities
         */
        me.application.addListener('DRSI.Training.Peruna.dafSaved', function (a, b, c, d) {
            
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

        me.stackForm = Ext.widget('addStack');
        me.stackForm.show();

        if (typeof record !== 'undefined') {
            console.log(record);
            me.stackForm.down('form').getForm().loadRecord(record);
        }
    },

    showProfileForm: function (record) {
        var me = this; 

        if (!me.hasOwnProperty('profileForm')) {
            me.profileForm = Ext.widget('addProfile');
        }

        me.profileForm.show();

        if (typeof record !== 'undefined') {
            console.log(record);
            me.profileForm.down('form').getForm().loadRecord(record);
        }
    },

    showAccountForm: function (record) {
        var me = this; 

        if (!me.hasOwnProperty('accountForm')) {
            me.accountForm = Ext.widget('addAccount');
        }

        me.accountForm.show();

        if (typeof record !== 'undefined') {
            console.log(record);
            me.accountForm.down('form').getForm().loadRecord(record);
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
        'Title'
        ,'account.List'
        ,'account.Add'
        ,'profile.List'
        ,'profile.Add'
        ,'stack.List'
        ,'stack.Add'
        ,'stack.HostContextMenu'
        ,'host.Add'
        ,'role.List'
    ],

    models: [
        'AccountProfile'
        ,'Host'
        ,'InstanceSize'
        ,'ProfileScript'
        ,'ProviderAccount'
        ,'ProviderType'
        ,'Role'
        ,'Stack'
    ],

    stores: [
        'AccountProfiles'
        ,'Hosts'
        ,'StackHosts'
        ,'InstanceSizes'
        ,'ProfileScripts'
        ,'ProviderAccounts'
        ,'ProviderTypes'
        ,'Roles'
        ,'Stacks'
    ],


    /*

             ____    _____   _____   _____   ____    _____   _   _    ____   _____   ____  
            |  _ \  | ____| |  ___| | ____| |  _ \  | ____| | \ | |  / ___| | ____| / ___| 
            | |_) | |  _|   | |_    |  _|   | |_) | |  _|   |  \| | | |     |  _|   \___ \ 
            |  _ <  | |___  |  _|   | |___  |  _ <  | |___  | |\  | | |___  | |___   ___) |
            |_| \_\ |_____| |_|     |_____| |_| \_\ |_____| |_| \_|  \____| |_____| |____/ 

    */
    refs: [{
        ref: 'newAccountButon', selector: '#results-panel'
    }]
});


