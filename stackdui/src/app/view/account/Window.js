Ext.define('stackdio.view.account.Window', {
    extend: 'Ext.window.Window'
    ,alias: 'widget.accountWindow'

    ,title: 'Provider Accounts'
    ,width: 500
    ,height: 400
    ,closeAction: 'hide'

    ,items: [
        { 
            xtype: 'accountList'
        }
    ]

    ,tbar: [
        {
            xtype: 'splitbutton'
            ,text: 'Add Account'
            ,id: 'create-account'
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


