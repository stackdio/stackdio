if (Meteor.isClient) {
    Roles = new Meteor.Collection("roles");

    // Template.stackForm.roles = function () {
    //     return Roles.find({}).fetch();
    // }
}