Ext.define('stackdio.view.profile.Window', {
    extend: 'Ext.window.Window'
    ,alias: 'widget.profileWindow'

    ,title: 'Account Profiles'
    ,width: 500
    ,height: 400
    ,closeAction: 'hide'

    ,items: [
        { 
            xtype: 'profileList'
        }
    ]

    ,tbar: [
        {
            xtype: 'splitbutton'
            ,text: 'Add Profile'
            ,id: 'create-profile'
            ,menu: {}
        }
    ]

    ,buttons: [{
        text: 'Close',
        iconCls: 'cancel-icon',
        handler: function (btn) {
            btn.up('window').hide();
        }
    }]
});


