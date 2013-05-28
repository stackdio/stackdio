if (Meteor.isClient) {
    Hosts = new Meteor.Collection("hosts");

    Template.hostList.hosts = function () {
        return Hosts.find({}).fetch();
    }
}
