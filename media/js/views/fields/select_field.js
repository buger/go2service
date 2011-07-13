var SelectFieldView = FieldView.extend({
    config_fields: [
        { type:"ref", label:"Родительский справочник", id: "ref" },
        { type:"checkbox", label:"Разрешить пустое значение", id:"show_null" },
        { type:"checkbox", label:"Работать как кактегория", id:"act_as_parent" }
    ],

    template: _.template([
        "<select>",
        "<% for (i in options) { %>",
        "<option value='<%=options[i][0]%>' <% if (value == options[i][0]) { %> selected <% } %>><%=options[i][1]%></option>",
        "<% } %>",
        "</select>"
    ].join('\n')),

    initialize: function(opts){
        var self = this;

        if (!this.model) 
            this.model = new Backbone.Model;
        
        if (!opts['options']) {
            if (this.model.get('config')) {
                this.ref_tree_item = new TreeItemModel()

                this.model.set({'options': [['','Загрузка...']]});
                this.ref_tree_item.set({'id':this.model.get('config')['ref']});

                this.ref_tree_item.fetch({
                    success: function(){
                        var options = self.ref_tree_item.get('children').map(function(ref){ return [ref.id, ref.get('name')] });

                        if (self.model.get('config')['show_null']) {
                            options.splice(0, 0, ['','']);
                        }

                        self.model.set({ 'options': options }, { silent:true });
                        self.render();
                        self.model.unset('options');
                    }
                });
            } else {
                this.model.set({'options': []});
            }
        } else {
            this.model.set({'options': opts['options']});
        }

        this._super('initialize', opts);
    }
});

