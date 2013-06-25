Ext.define('stackdio.view.stack.Add', {
    extend  : 'Ext.window.Window',
    alias: 'widget.addStack',
    
    width   : 800,
    title   : 'Stack',
    modal   : true,
    closable: true,
    closeAction: 'hide',
    defaultFocus: 'stack-title',

    defaults: {},
    layout: 'anchor',

    items: [
        {
            xtype: 'form',
            layout: 'anchor',
            padding: '10',
            border: false,
            anchor: '100% 70%',
            defaults: {
                anchor: '100%'
            },
            id: 'stack-form',
            items: [
            {
                xtype:'textfield',
                id: 'stack-title',
                name: 'title',
                fieldLabel: 'Title',
                labelWidth: 110,
                enableKeyEvents: true
            },{
                xtype:'textareafield',
                id: 'stack-description',
                name: 'description',
                fieldLabel: 'Description',
                labelWidth: 110,
                enableKeyEvents: true
            }]
        },
        {
            xtype: 'splitbutton'
            ,id: 'create-stack-host'
            ,text: 'New Host'
            ,ui: 'info'
            ,scale: 'small'
            ,iconCls: 'icon-plus-sign'
            ,style: 'float: right; margin: 10px 10px 0 0'
            ,menu: {}
            ,width: 130
        },
        {
            xtype:'grid',
            id: 'stack-hosts',
            autoScroll: true,
            store: 'StackHosts',
            anchor: '100% 30%',
            padding: '10',
            stripeRows: true,
            columns: [
                {
                    header: 'Roles',
                    dataIndex: 'roles',
                    flex: 2
                    ,renderer: function (ids, metaData, record, rowIndex, colIndex, store, view) {
                        var r, rr = [], store = Ext.getStore('Roles'), k = ids.split(',');

                        if (k.length && k[0] !== '') {
                            for (r in k) {
                                rr.push(store.getAt(store.findExact('id', parseInt(k[r], 10))).data.title);
                            }
                        }

                        return rr.join(',');
                    }
                },
                {
                    header: 'Count',
                    dataIndex: 'count',
                    flex: 1
                },
                {
                    header: 'Profile',
                    dataIndex: 'cloud_profile',
                    flex: 2
                    ,renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                        var store = Ext.getStore('AccountProfiles'), title = '', index = store.findExact('id', id);

                        console.log(index);
                        if (~index) {
                            title = store.getAt(index).data.title;
                        } 

                        return title;
                    }
                },
                {
                    header: 'Size',
                    dataIndex: 'instance_size',
                    flex: 3
                    ,hidden: true
                    ,renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                        var store = Ext.getStore('InstanceSizes'), size = '', index = store.findExact('id', id);

                        if (~index) {
                            size = store.getAt(index).data.title;
                        }

                        return '<div style="white-space:normal !important;">' + size + '</div>';
                    }
                },
                {
                    header: 'Host Pattern'
                    ,dataIndex: 'hostname'
                    ,flex: 1
                    ,hidden: true
                },
                {
                    header: 'Security Groups'
                    ,dataIndex: 'security_groups'
                    ,flex: 2
                    ,hidden: true
                }
            ]
        }
    ],

    buttons: [{
        text: 'Cancel',
        iconCls: 'cancel-icon',
        handler: function (btn) {
            btn.up('window').destroy();
        }
    },{
        text: 'Save',
        id: 'save-stack',
        iconCls: 'save-icon'
    }]
});

