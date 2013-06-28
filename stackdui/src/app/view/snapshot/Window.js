Ext.define('stackdio.view.snapshot.Window', {
    extend: 'Ext.window.Window'
    ,alias: 'widget.snapshotWindow'

    ,title: 'Snapshots'
    ,width: 500
    ,height: 400
    ,closeAction: 'hide'

    ,items: [
        { 
            xtype: 'snapshotList'
        }
    ]

    ,tbar: [
        {
            xtype: 'splitbutton'
            ,text: 'Add Snapshot'
            ,id: 'create-snapshot'
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


