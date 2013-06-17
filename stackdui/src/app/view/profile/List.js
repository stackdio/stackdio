Ext.define('stackdio.view.profile.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.profileList',
    store: 'AccountProfiles',

    autoScroll: true,
    features: [{
        ftype:'grouping',
        groupHeaderTpl: 'Provider: {cloud_provider}',
        startCollapsed: true,
        id: 'typeGrouping'
    }],

    // tbar: [
    //     {
    //         xtype: 'button',
    //         text: 'New Profile',
    //         iconCls: 'add-icon',
    //         id: 'create-profilez'
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


