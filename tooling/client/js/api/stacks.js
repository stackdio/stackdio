if (Meteor.isClient) {
    Stacks = new Meteor.Collection("stacks");

    Template.stackList.stacks = function () {
        return Stacks.find({}).fetch();
    }
}
