if (Meteor.isClient) {

    // Template.help.events({
    //     'click button': function () {
    //         console.log('vefvdfw')
    //     }        
    // });

    
    $('#role-help').popover({
        title: 'Salt Roles',
        content: 'Select one of the roles that you defined in your Salt tree, and the states for that role will be provisioned in this Stack.'
    });

    // Template.roleHelp.events({
    //     'popover button' : function () {
    //       // template data, if any, is available in 'this'
    //       if (typeof console !== 'undefined')
    //         console.log("You pressed the button");
    //     }
    // });
}

if (Meteor.isServer) {
  Meteor.startup(function () {
    // code to run on server at startup
  });
}


