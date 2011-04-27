var TreeItemModel = Backbone.Model.extend({
    url: function() {
        return "/service/ref/tree/" + (this.id || "");
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

var tree_item_tmpl = "<div>"+
                        "<a class='add' href='#add/<%=id%>'>(+)</a>"+
                        "<span class='toggle'></span>"+
                        "<a class='name' href='#edit/<%=id%>'><%= name || 'Без названия' %></a>"+
                     "</div>"+
                     "<ol></ol>";


var TreeItemView = Backbone.View.extend({

    tagName: "li",

    events: {
        "click .toggle:first" : "toggle"
    },

    template: _.template(tree_item_tmpl),

    initialize: function() {
        _.bindAll(this, 'render', 'addChild');
        this.model.bind('change', this.render);
        this.model.view = this;

        if (this.model.id != 'root') {
            $(this.el).addClass('closed');
        }

        this.el.view = this;
        $(this.el).addClass("node-" + this.model.id);
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        var container = this.$('ol:first');
                
        this.model.get('children').each(this.addChild);

        if (this.model.get('group')) {
            $(this.el).addClass('group');
        }
        
        if (store.get("tree-state-" + this.model.id) && $(this.el).hasClass('closed'))
            this.toggle();

        return this;
    },

    addChild: function(child) {
        var view = new TreeItemView({ model: child });
        this.$('ol:first').append(view.render().el);
    },

    toggle: function() {
        if (!this.model.get('loaded')) {
            this.$('ol:first').html('Loading...');
            
            this.model.fetch();
        }        

        $(this.el).toggleClass('closed');

        if ($(this.el).hasClass('closed'))
            store.remove("tree-state-" + this.model.id)
        else
            store.set("tree-state-" + this.model.id, "opened")
    }
});

var TreeView = Backbone.View.extend({
    initialize: function() {
        _.bindAll(this, "render");    
    },    

    render: function() {
        // Fetching root
        var model = new TreeItemModel({ id: 'root', name:'Корень', group: true});    
        var view = new TreeItemView({ model: model });
        $(this.el).html(view.render().el);        

        model.fetch();

        return this;
    },

    destroy: function(id) {
        $('.node-'+id).each(function(idx, el){
            el.view.remove();
        });
    }
});

var RefModel = Backbone.Model.extend({
    url: function(){
        return "/service/ref/" + this.id
    },

    parse: function(data){
        data['props'] = new PropertyCollection(data['props'])
        this.set(data);
    }
});


var FieldView = Backbone.View.extend({
    tagName: 'li',

    events: {
        "click .delete_field": "remove_field",
        "change label input": "change_label",
        "change span.field input": "change_value"
    },

    render: function() {
        if (this.model.get('locked')) {
            var label_text = this.model.get('label') || ref_form_names[this.model.id];
        } else {
            var label_text = this.make("input", {value: this.model.get('label'), type: 'text'});
        }
        
        var label = this.make("label", { for: this.model.id }, label_text);
        
        var field_container = this.make("span", {class:'field'}, this.template(this.model.toJSON()));
        $(this.el).append(label)
            .append(field_container);
        
        if (!this.model.get('locked')) {
            var delete_link = this.make("a", {class: 'delete_field'}, "✕");
            $(this.el).append(delete_link);
        } else {
            if (this.model.get('inherited_from')) {
                var info = this.make('span', {class: 'info', title:"Унаследовано от "+this.model.get('inherited_from')}, 'i');
                $(this.el).append(info);
            }
        }

        return this;
    },

    remove_field: function(){
        if (confirm('Внимание! Данное поле также удалится у всех дочерних элементов. Продолжить?')) {
            ref_form.model.get('props').remove(this.model);
            this.remove();
        }
    },

    change_value: function(){
        this.model.set({'value': this.$('.field input').val() });
    },

    change_label: function(){
        this.model.set({'label': this.$('label input').val() });
    }
});

var StaticFieldView = FieldView.extend({
    template: _.template("<%= value %>")
});

var TextFieldView = FieldView.extend({
    template: _.template("<input name='<%=name%>' value='<%=value%>' type='text' />")
});

var LinksFieldView = FieldView.extend({
    template: _.template([
        "<% for (i in value) { %>",
        "<a href='#edit/<%=value[i][0]%>'><%=value[i][1]%></a>",
        "<% } %>"
        ].join('\n'))
});

var Property = Backbone.Model.extend({
});

var PropertyCollection = Backbone.Collection.extend({
    model: Property
});

var current_ref = new RefModel({props: new PropertyCollection()});

var ref_form_names = {
    num_id: "Идентификатор",
    name: "Наименование",
    parents: "Родители",
    ancestors: "Все предки"
};

var RefForm = Backbone.View.extend({

    tagName: 'form',

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

    getTag: function(model) {
        var tagTypes = {
            'static': StaticFieldView,
            'text': TextFieldView,
            'links': LinksFieldView
        };
       
        var tag = tagTypes[model.get('type')];
        if (!tag)
            tag = StaticFieldView;

        return new tag({model: model});
    },

    updateTree: function(is_new){
        var self = this;

        function update_tree_item(key){
            $('.node-' + key).each(function(idx, el){
                el.view.model.set({ 'group': true });
                el.view.model.fetch({
                    success: function(){
                        if ($(el).hasClass('closed'))
                            el.view.toggle();    
                    }    
                });
            });
        }

        $('.node-' + self.model.id).each(function(idx, el){
            el.view.model.set({ name: self.model.get('name') });
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

    render: function() {
        var self = this;
        
        var container = this.make("ol");
        
        if (!this.model.get('props'))
            this.model.set({ 'props': new PropertyCollection() });

        this.model.get('props').each(function(prop) {
            var tag = self.getTag(prop);
            
            container.appendChild(tag.render().el);
        });
        
        var fieldset = this.make("fieldset", {}, container);

        var form = this.make("form", {
            action: "/service/ref/"+this.model.id,
            method: "POST"
        }, fieldset);
        
        var add_field = this.make("a", { class:'add_field', href:"javascript:;" }, "Добавить поле");
        var field_type = this.make("select", { class:"field_type" });
        _({'text': 'Текстовое поле'}).each(function(value, key){
            field_type.appendChild(self.make("option", {value: key}, value));
        });
 
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

        $(form).submit(function(){
            var is_new = self.model.id == 'new';

            self.model.save({}, {
                success: function(model, response) {
                    self.updateTree(is_new);
                    self.render();
                    ref_workspace.saveLocation("edit/"+model.id);
                }
            });

            return false;
        });
        
        $(this.el).html(form);
    }
});

var ref_form;
var ref_tree;

var tree = $('.tree');

ref_tree = new TreeView({ el: tree.find('ol') }).render();
ref_form = new RefForm({ el: tree.find('div'), model: current_ref });

var RefWorkspace = Backbone.Controller.extend({
    routes: {
        "edit/:key": "edit",
        "add/:key": "add"
    },

    edit: function(key) {
        ref_form.edit(key);
    },

    add: function(key) {
        ref_form.add(key);
    }
});
var ref_workspace = new RefWorkspace();
Backbone.history.start();

