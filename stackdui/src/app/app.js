"use strict"

Ext.require([
    'Ext.button.Split',
    'Ext.chart.Chart',
    'Ext.chart.axis.Numeric',
    'Ext.chart.axis.Category',
    'Ext.chart.series.Line',
    'Ext.container.ButtonGroup',
    'Ext.container.Viewport',
    'Ext.layout.container.Anchor',
    'Ext.layout.container.Border',
    'Ext.layout.container.Column',
    'Ext.layout.container.Form',
    'Ext.menu.Menu',
    'Ext.form.field.ComboBox',
    'Ext.form.field.Text',
    'Ext.form.field.Radio',
    'Ext.form.Panel',
    'Ext.form.RadioGroup',
    'Ext.grid.column.Action',
    'Ext.grid.column.Template',
    'Ext.grid.plugin.DragDrop',
    'Ext.grid.RowNumberer',
    'Ext.resizer.Splitter',
    'Ext.selection.CheckboxModel',
    'Ext.toolbar.Spacer',
    'Ext.util.Cookies',
    'Ext.util.MixedCollection',
    'Ext.util.AbstractMixedCollection',
    'Ext.util.Filter',
    'Ext.util.Observable',
    'Ext.util.Sorter',
    'Ext.util.Sortable',
    'Ext.ux.form.MultiSelect',
    'Ext.ux.RowExpander',
    'feature.grouping',
    'feature.rowbody',
    'feature.feature',
    'feature.rowwrap',
    'stackdio.tool.AnimatedMessage',
    'stackdio.tool.AuthenticatedConnection',
    'stackdio.tool.HowlNotification'
]);

var StackdIO;

Ext.onReady(function () {

    StackdIO = Ext.widget('apiRequest');

    Ext.application({
        controllers: [
            'Application'
            ,'Account'
            ,'Profile'
            ,'Stack'
            ,'Volume'
            ,'Snapshot'
        ],

        name: 'stackdio',
        autoCreateViewport: true,

        launch: function() {
            var me = this;

            me.notification     = Ext.widget('howler', { parentEl: 'title-panel' });
            me.animatedMessage  = Ext.widget('notify');
            me.settings         = {};

            me.settings.api_url = '';

            // Enable the focus manager
            Ext.FocusManager.enable();

            me.commandKeyMap = new Ext.util.KeyMap(Ext.getBody(), [
                {
                    key: "k",
                    alt: true,
                    shift: false,
                    handler: function (code, e) {
                        me.fireEvent('stackdio.showstacks');
                    }
                }
                ,{
                    key: "a",
                    alt: true,
                    shift: false,
                    handler: function (code, e) {
                        me.fireEvent('stackdio.showaccounts');
                    }
                }
                ,{
                    key: "p",
                    alt: true,
                    shift: false,
                    handler: function (code, e) {
                        me.fireEvent('stackdio.showprofiles');
                    }
                }
                ,{
                    key: "s",
                    alt: true,
                    shift: false,
                    handler: function (code, e) {
                        me.fireEvent('stackdio.showsnapshots');
                    }
                }
            ]);
        }
    });
});