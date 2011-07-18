// Getting ref tree using recursion
function getTree(tree_item, callback, all_children, level){
    if (!all_children) {
        level = 0;
        all_children = [];
    }

    var finished = 0;
    
    var complete_callback = function(){
        finished += 1;

        if (callback && finished == tree_item.get('children').length) {
            callback(all_children);
        }
    }
    
    if (tree_item.get('group')) {
        tree_item.get('children').map(function(ref){
            ref.set({ 'level':level });
            all_children.push(ref);

            ref.fetch({
                success: function(){
                    getTree(ref, function(){
                        complete_callback();
                    }, all_children, level+1);
                }
            });
        });
    } else {
        callback(all_children);        
    }
}


String.prototype.repeat = function( num ) {
    return new Array( num + 1 ).join( this );
}


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
                        self.ref_tree_item.set({ 'group': true });

                        getTree(self.ref_tree_item, function(children){
                            var options = _(children).map(function(ref){ 
                                // Repeat spaces based on ref level
                                var label = "&nbsp;&nbsp;&nbsp;&nbsp;".repeat(ref.get('level')) + ref.get('name');
                                return [ref.id, label];
                            });

                            if (self.model.get('config')['show_null']) {
                                options.splice(0, 0, ['','']);
                            }

                            self.model.set({ 'options': options }, { silent:true });
                            self.render();
                            self.model.unset('options');
                        });
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

