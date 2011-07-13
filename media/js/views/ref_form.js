var ref_form_names = {
    num_id: "Идентификатор",
    name: "Наименование",
    parents: "Родители",
    ancestors: "Все предки"
};

function update_tree_item(key){
    $('.node-' + key).each(function(idx, el){
        el.view.model.set({ 'group': true });
        el.view.model.fetch({
            success: function(){
                el.view.open();    
            }    
        });
    });
}

var RefForm = BaseForm.extend({
    initialize: function() {
        _.bindAll(this, "edit", "render", "updateTree");
        
        this.model.bind("change:id", this.render);
    },
    
    add: function(id) {
        this.model.clear({ silent: true });
        this.model.id = "new?parent="+id
        this.model.fetch();
    },

    edit: function(id) {
        this.model.clear({ silent: true });
        this.model.id = id;
        this.model.fetch();
    },

    destroy: function(id){
        this.model.set({id : id}, { silent: true} );
        this.model.destroy();

        $(this.el).html('');
    },

    updateTree: function(is_new){
        var self = this;

        $('.node-' + self.model.id).each(function(idx, el){
            el.view.model.set({ name: self.model.get('name') });
            $(el).find('a.name').html(self.model.get('name'));
        });
        
        if (is_new) {            
            if (self.model.get('parents').length == 0) {
                update_tree_item('root');
            }

            _(self.model.get('parents')).each(function(item){
                update_tree_item(item[0])
            });
        }
    },

    activateTree: function(){        
        try {
            var tree_item = $('.node-' + this.model.id)[0].view.open();
        } catch(e) {}
    },

    render: function() {
        var self = this;
        
        this.el.empty();

        var container = this.make("ol");
        
        if (!this.model.get('props'))
            this.model.set({ 'props': new PropertyCollection() });

        this.model.get('props').each(function(prop) {
            var tag = self.getTag(prop);
            
            container.appendChild(tag.render().el);
        });
        
        var fieldset = this.make("fieldset", {}, container);
        
        var form = this.make("form", { 'class':'form' });
        form.action = "/service/ref/"+this.model.id;
        form.method = "POST";

        form.appendChild(fieldset);
        
        var add_field = this.make("a", { 'class':'add_field', href:"javascript:;" }, "Добавить поле");
        
        var field_type = this.fieldTypesSelect();

        $(add_field).bind('click', function(){
            var type = field_type.options[field_type.selectedIndex].value;
            self.model.get('props').add({id: +new Date, label: "Без названия", type: type, value: "" });
            self.render();
        });

           
        var add_field_container = this.make("div")
        add_field_container.appendChild(field_type)
        add_field_container.appendChild(add_field)
        
        form.appendChild(add_field_container);
        
        var save_button = this.make("input", { 
            type: 'submit', 
            value: this.model.id == 'new' ? "Добавить" : "Сохранить"
        });
        form.appendChild(save_button);

        if (this.model.id != 'new') {
            var delete_link = this.make("a", {'class': "delete"}, "Удалить");            
            $(delete_link).bind('click', function(){
                if (confirm("Удалить справочное значение?")) {
                    ref_form.destroy(self.model.id);
                    ref_tree.destroy(self.model.id);
                    ref_workspace.saveLocation("");
                }
            });
            form.appendChild(delete_link);         
        }

        $(form).bind('submit', function(){
            var is_new = self.model.id == 'new';

            self.model.save({}, {
                success: function(model, response) {
                    self.updateTree(is_new);
                    self.render();
                    ref_workspace.saveLocation("edit/"+model.id);
                },

                error: function(model, response) {
                    save_button.disabled = false;
                    save_button.value = "Сохранить";
                }
            });

            save_button.disabled = true;
            save_button.value = "Сохранение...";

            return false;
        });
        
        $(form).appendTo(this.el);
        
        this.activateTree();

        return this.el;
    }
});

