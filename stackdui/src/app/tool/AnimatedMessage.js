Ext.define('stackdio.tool.AnimatedMessage', {
    alias: 'widget.notify',
    msgCt: undefined,

    abstractBox: function (title, message, delay, type) {
        var s, box, clazz;

        if(!this.msgCt){
            this.msgCt = Ext.core.DomHelper.insertFirst(document.body, {id:'msg-div'}, true);
        }

        Ext.core.DomHelper.applyStyles(this.msgCt, {
            top:  (window.innerHeight / 2 - 100) + window.pageYOffset + 'px',
            left: (window.innerWidth / 2 - 150) + window.pageXOffset + 'px'
        });
        
        switch (type) {
            case 'error':
                clazz = 'error-msg';
                break;

            case 'message':
                clazz = 'standard-msg';
                break;
        }

        box = Ext.core.DomHelper.append(this.msgCt, '<div class="' + clazz + ' box-shadow"><h3>' + title + '</h3><p>' + message + '</p><div class="msg-bottom"></div></div>', true);
        box.hide();
        box.slideIn('t', {
            duration: 750
        }).ghost('t', {
            delay: delay,
            remove: true
        });
    },

    msg : function(title, message, delay){
        this.abstractBox(title, message, delay, 'message');
    },

    error : function(title, message, delay){
        this.abstractBox(title, message, delay, 'error');
    }
});