var SelectFieldView = FieldView.extend({
    ref_tree_item: new TreeItemModel(),    

    config_fields: [
        { type:"ref", label:"Справочник", id: "ref" }
    ],

    template: _.template([
        "<select>",
        "<% for (i in options) { %>",
        "<option value='<%=options[i][0]%>'><%=options[i][1]%></option>",
        "<% } %>",
        "</select>"
    ].join('\n')),

    initialize: function(opts){
        var self = this;

        this.model.set({'options': [['','Загрузка...']]});

        this.ref_tree_item.set({'id':this.model.get('config')['ref']});
        
        this.ref_tree_item.fetch({
            success: function(){
                var options = self.ref_tree_item.get('children').map(function(ref){ return [ref.id, ref.get('name')] });
                self.model.set({ 'options': options }, { silent:true });
                self.render();
                self.model.unset('options');
            }
        });

        this._super('initialize', opts);
    }
});

