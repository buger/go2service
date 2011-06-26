var RefWorkspace = Backbone.Controller.extend({
    routes: {
        "edit/:key": "edit",
        "add/:key": "add",
        "import/:key": "import"
    },

    edit: function(key) {
        ref_form.edit(key);
    },

    add: function(key) {
        ref_form.add(key);
    },

    import: function(key) {
        new ImportForm({ model: new ImportModel({root: key}) });
    }
});

var ref_workspace = new RefWorkspace();
Backbone.history.start();
