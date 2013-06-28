Ext.define('stackdio.view.volume.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addVolume',
    
    width   : 800,
    title   : 'Attachable Volume',
    modal   : true,
    closable: true,
    closeAction: 'hide',
    defaultFocus: 'volume-title',

    defaults: {
        padding: '10'
    },

    layout: 'fit',

    items: [{
        xtype: 'form',
        id: 'volume-form',
        border: false,
        layout: 'anchor',
        defaults: {
            anchor: '100%'
        },
        items: [
            {
                xtype:        'combo',
                name:         'snapshot',
                hideLabel:    false,
                fieldLabel:   'Snapshot',
                labelWidth:   110,
                store:        'Snapshots',
                displayField: 'title',
                valueField:   'id',
                queryMode:    'local',
                editable:     false
            }
            ,{
                xtype:'textfield',
                name: 'device',
                fieldLabel: 'Device',
                labelWidth: 110,
                enableKeyEvents: true
            }
            ,{
                xtype:'textfield',
                name: 'mount_point',
                fieldLabel: 'ID',
                labelWidth: 110
            }
        ]
    }],

    buttons: [{
        text: 'Cancel',
        iconCls: 'cancel-icon',
        handler: function (btn) {
            btn.up('window').hide();
        }
    },{
        text: 'Save',
        id: 'save-host-volume',
        iconCls: 'save-icon'
    }]
});

