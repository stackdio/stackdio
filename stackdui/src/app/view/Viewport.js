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
        height: 80
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
            anchor: '100%'
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
                id: 'stacks-button',
                text: 'Stacks',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-tasks'
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
                iconCls: 'icon-user'
            },
            {
                id: 'roles-button',
                text: 'Roles',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-user'
            },
            {
                id: 'volumes-button',
                text: 'Snapshots',
                ui: 'default',
                scale: 'medium',
                iconCls: 'icon-camera',
                style: 'text-align:left;'
            }
        ]
    },{
        region: 'center',
        xtype: 'panel',
        id: 'content-area',
        title: false,
        border: false,

        items: [
            // {
            //     xtype: 'container'
            //     ,cls: 'nav-bar'
            //     ,html: [
            //             '<div class="tip">Accounts  (alt+a)</div>',
            //             '<div class="tip">Profiles  (alt+p)</div>',
            //             '<div class="tip">Snapshots (alt+s)</div>',
            //             '<div class="tip">Stack (alt+k)</div>',
            //             '<div class="tip">Help (alt+?)</div>'
            //            ].join('')
            // },
            {
                xtype: 'container',
                cls: 'main-body',
                items: [
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
                    }
                ]
            }
        ]
    }]
});