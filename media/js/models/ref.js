var RefModel = Backbone.Model.extend({
    url: function(){
        return "/service/ref/" + this.id
    },

    parse: function(data){
        data['props'] = new PropertyCollection(data['props'])
        this.set(data);
    }
});

