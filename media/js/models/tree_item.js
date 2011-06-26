var TreeItemModel = Backbone.Model.extend({
    url: function() {
        return "/service/ref/tree/" + (this.id || "") + "?import_id=" + (this.get('import_id')||"");
    },    

    initialize: function() {
        if (!this.get('children')) {            
            this.set({'children' : new TreeItemCollection()});
        }
    },

    parse: function(response) {
        this.set({        
            children : new TreeItemCollection(response.children),
            loaded   : true
        });
    }
});

var TreeItemCollection = Backbone.Collection.extend({
    model: TreeItemModel
});
