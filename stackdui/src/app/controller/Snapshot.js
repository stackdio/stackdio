Ext.define('stackdio.controller.Snapshot', {
    extend: 'Ext.app.Controller',


    init: function () {
        var me = this;

        me.snapshotWindow = Ext.widget('snapshotWindow');


        /*

              ____ ___  _   _ _____ ____   ___  _        _     ___   ____ ___ ____ 
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |      | |   / _ \ / ___|_ _/ ___|
            | |  | | | |  \| | | | | |_) | | | | |      | |  | | | | |  _ | | |    
            | |__| |_| | |\  | | | |  _ <| |_| | |___   | |__| |_| | |_| || | |___ 
             \____\___/|_| \_| |_| |_| \_\\___/|_____|  |_____\___/ \____|___\____|

        */
        me.control({

            '#save-snapshot': {
                click: function (btn, e) {
                    var verb, urlSuffix = '', r, rec, record = me.snapshotForm.down('form').getForm().getValues();

                    if (record.hasOwnProperty('id')) {
                        verb = 'PUT';
                        urlSuffix = me.selectedProfile.data.id + '/';
                    } else {
                        verb = 'POST';
                    }

                    record.cloud_provider = me.providerAccount;

                    StackdIO.request({
                        url: '/api/snapshots/' + urlSuffix,
                        method: verb,
                        jsonData: record,
                        success: function (response) {
                            var res = Ext.JSON.decode(response.responseText);

                            if (res.hasOwnProperty('id')) {
                                me.application.notification.howl('Snapshot saved...', 2000);
                                btn.up('window').hide();
                                me.getSnapshotsStore().load();
                            } else {
                                me.application.notification.scold('Snapshot did not save. Update your data and try again', 3000);
                            }
                        },
                        failure: function (response) {
                            me.application.notification.scold('Snapshot did not save. Update your data and try again', 3000);
                        }
                    });
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
        me.getProviderAccountsStore().on('load', function (store, records, successful, eOpts) {
            var t, type, types;
            var btn = me.getCreate();

            for (t in records) {
                type = records[t];
                btn.menu.add({
                    text: type.data.title,
                    id: 'snapshotaccount-' + type.data.id,
                    handler: function () {
                        me.application.fireEvent('stackdio.newsnapshot', this.id.split('-')[1]);
                    }
                })
            }
        });

        me.application.addListener('stackdio.newsnapshot', function (accountId) {
            me.providerAccount = accountId;
            me.showSnapshotForm();
        });

        me.application.addListener('stackdio.showsnapshots', function () {
            me.snapshotWindow.show();
        });
    },



    /*

              ____ ___  _   _ _____ ____   ___  _     _     _____ ____     _____ _   _ _   _  ____ _____ ___ ___  _   _ ____  
             / ___/ _ \| \ | |_   _|  _ \ / _ \| |   | |   | ____|  _ \   |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___| 
            | |  | | | |  \| | | | | |_) | | | | |   | |   |  _| | |_) |  | |_  | | | |  \| | |     | |  | | | | |  \| \___ \ 
            | |__| |_| | |\  | | | |  _ <| |_| | |___| |___| |___|  _ <   |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
             \____\___/|_| \_| |_| |_| \_\\___/|_____|_____|_____|_| \_\  |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/ 

    */

    showSnapshotForm: function (record) {
        var me = this; 

        if (!me.hasOwnProperty('snapshotForm')) {
            me.snapshotForm = Ext.widget('addSnapshot');
        }

        me.snapshotForm.show();

        if (typeof record !== 'undefined') {
            me.snapshotForm.down('form').getForm().loadRecord(record);
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
         'snapshot.Add'
        ,'snapshot.List'
        ,'snapshot.Window'
    ],

    models: [
        'Snapshot'
    ],

    stores: [
         'Snapshots'
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
            ref: 'create', selector: '#create-snapshot'
        }
        ,{
            ref: 'save', selector: '#save-snapshot'
        }
    ]
});


