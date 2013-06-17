Ext.define('stackdio.tool.HowlNotification', {
    msgCt: undefined,
    alias: 'widget.howler',

    config: {
        parentEl: undefined
    },

    constructor: function(cfg) {
        this.initConfig(cfg);
    },

    abstractBox: function (type, message, delay) {
        var s, box, clazz, html='', me = this,
            parentEl = Ext.get(me.config.parentEl),
            boxTop = parentEl.getY() + parentEl.getHeight();

        if(!this.msgCt){
            this.msgCt = Ext.core.DomHelper.insertFirst(document.body, {id:'growl-div'}, true);
        }

        Ext.core.DomHelper.applyStyles(this.msgCt, {
            top:  boxTop + 'px',
            left: '0',
            width: parentEl.getWidth() + 'px'
        });
        
        clazz = 'howl-msg-' + type;
        html += '<div class="' + clazz + '">' + message + '</div>';

        box = Ext.core.DomHelper.append(this.msgCt, html, true);
        box.hide();

        box.slideIn('t', {
            easing: 'easeIn',
            duration: 500
        }).slideOut('t', {
            easing: 'easeOut',
            delay: delay,
            duration: 500,
            listeners: {
                afteranimate: function () {
                    box.destroy();
                }
            }
        });
    },

    howl: function(message, delay){
        this.abstractBox('standard', message, delay);
    },

    scold: function(message, delay){
        this.abstractBox('error', message, delay);
    }
});