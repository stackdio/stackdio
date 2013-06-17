Ext.define('stackdio.view.account.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.accountList',
    store: 'ProviderAccounts',

    autoScroll: true,
    features: [{
        ftype:'grouping',
        groupHeaderTpl: 'Provider: {provider_type_name}',
        startCollapsed: true,
        id: 'typeGrouping'
    }],

    // tbar: [
    //     {
    //         xtype: 'button',
    //         text: 'New Account',
    //         iconCls: 'add-icon',
    //         id: 'create-accountz'
    //     }
    // ],

    columns: [
        { 
            header: 'Title',
            dataIndex: 'title',
            flex: 1
        },
        { 
            header: 'Description',
            dataIndex: 'description',
            flex: 4
        }
    ]
});


