

function Stack(title, description, namespace, create_users, properties, blueprint) {
    var self = this;

    // Editable fields
    self.title = ko.observable(title);
    self.description = ko.observable(description);
    self.create_users = ko.observable(create_users);
    self.properties = ko.observable(properties);

    // Non-editable fields
    self.namespace = namespace;
    self.blueprint = blueprint;
}