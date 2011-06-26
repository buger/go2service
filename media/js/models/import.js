var ImportModel = Backbone.Model.extend({
    url: function() {
        return "/service/ref/import/" + this.get('root');
    } 
});

