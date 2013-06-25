Ext.define('stackdio.view.Viewport', {
    renderTo: Ext.getBody(),
    extend: 'Ext.container.Viewport',
    requires:[
        'Ext.tab.Panel',
        'Ext.layout.container.Border'
    ],

    layout: {
        type: 'border'
    },

    items: [{
        region: 'north',
        xtype: 'title',
        id: 'title-panel',
        title: false,
        border: true,
        height: 60
    },{
        region: 'west',
        xtype: 'container',
        title: false,
        width: 190,
        border: true,
        layout: 'anchor',
        defaults: {
            xtype: 'button',
            margin: 4,
            anchor: '100%',
            style: {
                textAlign: 'left'
            }
        },

        items: [
            {
                id: 'dashboard-button',
                text: 'Dashboard',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-home'
            },
            {
                id: 'accounts-button',
                text: 'Providers Accounts',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-hdd'
            },
            {
                id: 'profiles-button',
                text: 'Account Profiles',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-off'
            },
            {
                id: 'stacks-button',
                text: 'Stacks',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-tasks'
            },
            {
                id: 'roles-button',
                text: 'Roles',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-user'
            }
        ]
    },{
        region: 'center',
        xtype: 'panel',
        id: 'content-area',
        title: false,
        border: false,
        margin: '10px 50px',
        layout: 'card',

        items: [
            {
                xtype: 'container',
                items: [
                    {
                        xtype: 'container',
                        layout: 'hbox',
                        items: [
                            {
                                xtype: 'container',
                                html: '<h3>Provider Accounts</h3>',
                                flex: 1
                            },
                            {
                                xtype: 'container',
                                items: {
                                    xtype: 'splitbutton',
                                    id: 'create-account',
                                    text: 'New Account',
                                    ui: 'info',
                                    iconCls: 'icon-plus-sign',
                                    width: 130,
                                    style: 'margin: 20px 0 0 0; float: right',
                                    menu: {}
                                },
                                flex: 1
                            }
                        ]
                    },
                    {
                        xtype: 'accountList',
                        id: 'accountList'
                    },
                    {
                        xtype: 'container',
                        layout: 'hbox',
                        items: [
                        {
                            xtype: 'container',
                            html: '<h3>Account Profiles</h3>',
                            flex: 1
                        },
                        {
                            xtype: 'container',
                            items: {
                                xtype: 'splitbutton',
                                id: 'create-profile',
                                width: 130,
                                text: 'New Profile',
                                ui: 'info',
                                iconCls: 'icon-plus-sign',
                                style: 'margin: 20px 0 0 0; float: right',
                                menu: {}
                            },
                            flex: 1
                        }
                        ]
                    },
                    {
                        xtype: 'profileList'
                    },
                    {
                        xtype: 'container',
                        layout: 'hbox',
                        items: [
                        {
                            xtype: 'container',
                            html: '<h3>Stacks</h3>',
                            flex: 1
                        },
                        {
                            xtype: 'container',
                            items: {
                                xtype: 'button',
                                id: 'create-stack',
                                width: 130,
                                text: 'New Stack',
                                ui: 'info',
                                iconCls: 'icon-plus-sign',
                                style: 'margin: 20px 0 0 0; float: right'
                            },
                            flex: 1
                        }
                        ]
                    },
                    {
                        xtype: 'stackList'
                    },
                    {
                        xtype: 'container',
                        layout: 'hbox',
                        items: [
                            {
                                xtype: 'container',
                                html: '<h3>Roles</h3>',
                                flex: 1
                            },
                            {
                                xtype: 'container',
                                items: {
                                    xtype: 'button',
                                    id: 'create-role',
                                    width: 130,
                                    text: 'New Role',
                                    ui: 'info',
                                    iconCls: 'icon-plus-sign',
                                    style: 'margin: 20px 0 0 0; float: right'
                                },
                                flex: 1
                            }
                        ]
                    },
                    {
                        xtype: 'roleList'
                    },
                    {
                        xtype: 'container',
                        layout: 'hbox',
                        items: [
                            {
                                xtype: 'container',
                                html: '<h3>Volumes</h3>',
                                flex: 1
                            },
                            {
                                xtype: 'container',
                                items: {
                                    xtype: 'button',
                                    id: 'create-volume',
                                    width: 130,
                                    text: 'New Volume',
                                    ui: 'info',
                                    iconCls: 'icon-plus-sign',
                                    style: 'margin: 20px 0 0 0; float: right'
                                },
                                flex: 1
                            }
                        ]
                    },
                    {
                        xtype: 'volumeList'
                    }
                ]
            }
        ]
    }]
});