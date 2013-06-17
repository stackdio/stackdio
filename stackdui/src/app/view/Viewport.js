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
        height: 45
    },{
        region: 'west',
        xtype: 'container',
        title: false,
        width: 190,
        border: true,
        layout: 'anchor',
        defaults: {
            xtype: 'button'
            ,margin: '0 4px'
            ,anchor: '100%'
        },
        style: {
            margin: '30px 10px'
        },

        items: [
            {
                id: 'dashboard-button'
                ,text: 'Dashboard'
                ,ui: 'default'
                ,scale: 'medium'
                ,iconCls: 'icon-home'
            },
            {
                id: 'accounts-button'
                ,text: 'Providers Accounts'
                ,ui: 'default'
                ,scale: 'medium'
                ,iconCls: 'icon-hdd'
            },
            {
                id: 'profiles-button'
                ,text: 'Account Profiles'
                ,ui: 'default'
                ,scale: 'medium'
                ,iconCls: 'icon-off'
            },
            {
                id: 'stacks-button'
                ,text: 'Stacks'
                ,ui: 'default'
                ,scale: 'medium'
                ,iconCls: 'icon-tasks'
            },
            {
                id: 'roles-button'
                ,text: 'Roles'
                ,ui: 'default'
                ,scale: 'medium'
                ,iconCls: 'icon-user'
            }
        ]
    },{
        region: 'center',
        xtype: 'panel',
        title: false,
        border: false,
        margin: '20px 50px',

        items: [
            {
                xtype: 'container',
                layout: 'hbox',
                items: [
                {
                    xtype: 'container'
                    ,html: '<h3>Provider Accounts</h3>'
                    ,flex: 1
                },
                {
                    xtype: 'container',
                    items: {
                        xtype: 'button'
                        ,id: 'create-account'
                        ,width: 120
                        ,text: 'New Account'
                        ,ui: 'info'
                        ,iconCls: 'icon-plus-sign'
                        ,style: {
                            margin: '20px 0 0 0'
                            ,float: 'right'
                        }
                    }
                    ,flex: 1
                }
                ]
            },
            {
                xtype: 'accountList'
            },
            {
                xtype: 'container',
                layout: 'hbox',
                items: [
                {
                    xtype: 'container'
                    ,html: '<h3>Account Profiles</h3>'
                    ,flex: 1
                },
                {
                    xtype: 'container',
                    items: {
                        xtype: 'button'
                        ,id: 'create-profile'
                        ,width: 120
                        ,text: 'New Profile'
                        ,ui: 'info'
                        ,iconCls: 'icon-plus-sign'
                        ,style: {
                            margin: '20px 0 0 0'
                            ,float: 'right'
                        }
                    }
                    ,flex: 1
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
                    xtype: 'container'
                    ,html: '<h3>Stacks</h3>'
                    ,flex: 1
                },
                {
                    xtype: 'container',
                    items: {
                        xtype: 'button'
                        ,id: 'create-stack'
                        ,width: 120
                        ,text: 'New Stack'
                        ,ui: 'info'
                        ,iconCls: 'icon-plus-sign'
                        ,style: {
                            margin: '20px 0 0 0'
                            ,float: 'right'
                        }
                    }
                    ,flex: 1
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
                    xtype: 'container'
                    ,html: '<h3>Roles</h3>'
                    ,flex: 1
                },
                {
                    xtype: 'container',
                    items: {
                        xtype: 'button'
                        ,id: 'create-role'
                        ,width: 120
                        ,text: 'New Role'
                        ,ui: 'info'
                        ,iconCls: 'icon-plus-sign'
                        ,style: {
                            margin: '20px 0 0 0'
                            ,float: 'right'
                        }
                    }
                    ,flex: 1
                }
                ]
            },
            {
                xtype: 'roleList'
            }
        ]
    }]
});