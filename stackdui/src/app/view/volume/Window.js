Ext.define('stackdio.view.volume.Window', {
    extend: 'Ext.window.Window'
    ,alias: 'widget.volumeWindow'

    ,title: 'Snapshots'
    ,width: 500
    ,height: 400
    ,closeAction: 'hide'

    ,items: [
        { 
            xtype: 'volumeList'
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


