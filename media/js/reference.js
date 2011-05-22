var ref_form;
var ref_tree;

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

var tree_item_tmpl = "<div class='item'>"+
                        "<div class='panel'><a href='#import/<%=id%>' class='import'>Импорт</a></div>"+
                        "<a class='add' href='#add/<%=id%>'>(+)</a>"+
                        "<a class='name'><%= name || 'Без названия' %></a>"+
                     "</div>";


var TreeItemView = Backbone.View.extend({

    tagName: "div",

    events: {
        "click .name:first": "edit"
    },

    template: _.template(tree_item_tmpl),

    initialize: function(opts) {
        _.bindAll(this, "render");

        this.model.view = this;
        
        this.el.view = this;
        $(this.el).addClass("node-" + this.model.id);

        if (this.model.get('state'))
            $(this.el).addClass("state-" + this.model.get('state'));

        if ($(this.el).hasClass('node-root')) {
            $(this.el).addClass('opened');
        }

        this.level = opts.level || 0;

        this.scroll = opts.scroll;
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        
        if (ref_form.model.id == this.model.id)
            $(this.el).addClass('opened');        

        if (this.model.get('group')) {
            $(this.el).addClass('group');
        }
        
        if ($(this.el).hasClass('opened')) {
            this.open();
        }
        
        return this;
    },

    renderChildren: function() {        
        var self = this;
        var container = $(this.el).parents('.wrapper').find('.level_'+(this.level+1));

        try {
            var scrollbar_api = $(this.el).parents('.wrapper').get(0).scrollbar_api;
        } catch(e) {
            console.log(this.el);
        }

        if (!this.model.get('group')) {
            container.empty();

            var previous_level = $(this.el).parents('.wrapper').find('.level_'+(this.level-1));

            scrollbar_api.reinitialise();
            scrollbar_api.scrollTo((self.level-2)*200);
        } else {
            if (!container[0]) {
                container = $("<div class='level level_"+(this.level+1)+"'></div>");
                scrollbar_api.getContentPane().append(container)

                container = $(this.el).parents('.wrapper').find('.level_'+(this.level+1));
            }

            container.empty();

            console.log('drawing childs', container)
            
            this.model.get('children').each(function(el){
                var view = new TreeItemView({ model: el, level: self.level+1, scroll: false});

                container.append(view.render().el);
            });

            scrollbar_api.reinitialise();
            scrollbar_api.scrollTo((self.level-1)*200);
        }
        
    },

    open: function(render) {
        var self = this;

        $(this.el).parents('.level').find('.opened').removeClass('opened');
        $(this.el).parents('.level').nextAll().find('.opened').removeClass('opened');
        $(this.el).addClass('opened');        

        if (!this.model.get('loaded')) {
            $(this.el).parents('.level').next().html('Загрузка...');
            
            this.model.fetch({silent: true, success: function(){ self.renderChildren()} });
        } else {
            this.renderChildren();
        }
        
        try {
            $(this.el).parents('.wrapper').get(0).view.updateLevelsHeader();
        } catch(e) {}
    },

    edit: function() {
        var self = this;

        if ($(this.el).parents('without-editing').length == 0) {
            document.location.hash = "#edit/"+self.model.id;
        }
        
        this.open();
    }
});

var TreeView = Backbone.View.extend({
    initialize: function() {
        _.bindAll(this, "render"); 
    },    

    render: function() {
        if (this.options['root']) {
            var model = new TreeItemModel({ id: this.options['root'], name:'', group: true, import_id: this.options['import_id']});
        } else {
            var model = new TreeItemModel({ id: 'root', name:'Корень', group: true});
        }

        var view = new TreeItemView({ model: model, className: this.options['root'] ? "node-root without-editing" : "" });
        $(this.el).html(view.render().el);        

        this.el.scrollbar_api = $(this.el).jScrollPane({ autoReinitialize: true, horizontalDragMinWidth: 200, horizontalDragMaxWidth: 200, animateScroll: true }).data('jsp');
        this.el.view = this;

        return this;
    },

    levels_template: _.template([
        '<% _.each(items, function(item){ %>',
        '<a href="#edit/<%=item.id%>"><%= item.get("name") %></a>',
        '<% }); %>'
    ].join('')),

    updateLevelsHeader: function(){
        var self = this;
        var container = $(this.el).parent().find('.levels_header');
        var opened = _.map(this.$('div.opened:visible'), function(el){ return el.view.model });

        container.html(this.levels_template({ items: opened }));

        container.find('a').bind('click', function() {
            var id = _.last(this.href.split("/"));
            var tree_item = self.$('.node-'+id);

            if (tree_item.get(0)) {
                var view = tree_item.get(0).view;

                var scrollbar_api = self.el.scrollbar_api;
                scrollbar_api.scrollTo((view.level-1) * 200);
            }
        });

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

    activateTree: function(){        
        var tree_item = $('.node-' + this.model.id).addClass('opened');
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

        this.activateTree();
    }
});


var ImportModel = Backbone.Model.extend({
    url: function() {
        return "/service/ref/import/" + this.get('root');
    } 
});

var ImportForm = Backbone.View.extend({
    tagName: 'div',
    className: 'import-form',    

    events: {    
        "change input[type='file']": "upload",
        "click .new-import": "new_import",
        "click .complete-import": "complete_import",
        "click .next-step": "next_step"
    },

    templates: {
        'init': _.template([
            "<label>Выберите CSV файл для импорта</label>",
            "<input type='file' />",
            "<div class='progress' style='display:none'><div class='bar'></div></div>"
        ].join('\n')),

        'processing': _.template([
            "<h3>Обработка записей</h3>",
            "<div><%=message%></div>",
            "<div class='progress'><div class='bar' style='width:<%=count/all_count*100%>%'></div></div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('\n')),

        'error': _.template([
            "<h3>Ошибка импорта</h3>",
            "<div><%=message%></div>",
            "<div class='new-import'>Начать новый импорт</div>"
        ].join('\n')),

        'merging': _.template([
            "<h3>Анализ загруженных данных</h3>",
            "<div><%=message%></div>",
            "<div class='progress'><div class='bar' style='width:<%=count/all_count*100%>%'></div></div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('\n')),

        'preview': _.template([
            "<h3>Предварительный просмотр",
                "<div class='complete-import'>Завершить импорт</div>",
            "</h3>",
            "<div class='legend'>",
                "<div class='new'>Новые</div>",
                "<div class='changed'>Измененные</div>",
                "<div class='unchanged'>Неизмененные</div>",
            "</div>",
            "<div class='tree'>",
                "<ol>Загрузка...</ol>",
            "</div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('\n')),

        'finalizing': _.template([
            "<h3>Обновление справочника</h3>",
            "<div class='progress'><div class='bar' style='width:<%=count/all_count*100%>%'></div></div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('\n')),
    },
    
    initialize: function(){
        _.bindAll(this, "render", "update_state");
        this.model.fetch();
        this.model.bind('change', this.render);
        this.model.bind('change', this.update_state);        
    },
    
    update_state: function(){
        var self = this;
        var state = this.model.get('state')

        if (state == 'processing' || state == 'merging' || state == 'finalizing') {
            clearInterval(this.refresh_timer);

            this.refresh_timer = setInterval(function(){
                self.model.fetch();
            }, 2000);
        } else {
            clearInterval(this.refresh_timer);
        }

        if (state == 'merging' && this.model.get('count') >= this.model.get('all_count')) {
            $.getJSON("/service/ref/import/"+this.model.id+"/set_state/preview", function(){});
            this.model.set({ state: 'preview' });
            
            clearInterval(this.refresh_timer);
        }
        
        if (state == 'finalizing' && this.model.get('count') >= this.model.get('all_count')) {
            clearInterval(this.refresh_timer);
            $.facebox.close();
            ref_workspace.saveLocation("");
            update_tree_item(this.model.get('root'));
            
            setTimeout(function(){
                self.model.destroy();
            }, 1000);
        }
    },

    render: function(){
        var template = this.templates[this.model.get('state')];
        var html = template(this.model.toJSON());        

        $(this.el).html(this.make("div", {className:this.model.get('state')}, html));

        $.facebox($(this.el));

        if (this.model.get('state') == 'preview') {
            new TreeView({ 
                el: $(this.el).find('.wrapper')[0], 
                root: this.model.get('root'), 
                import_id: this.model.id
            }).render();
        }

        this.delegateEvents();
    },
    
    next_step: function(){
        $.getJSON("/service/ref/import/"+this.model.id+"/set_state/preview", function(){});
        this.model.set({ state: 'preview' });
        
        clearInterval(this.refresh_timer);
    },

    new_import: function(){
        var self = this;
        var root = this.model.get('root');

        this.model.destroy({success: function(model, response){
            self.model.set({'root': root }, { silent: true });            
            self.model.fetch();
        }});
    },

    complete_import: function(){
        $.getJSON("/service/ref/import/"+this.model.id+"/set_state/finalizing", function(){});
        this.model.set({ state: 'finalizing', count: 0 });        
    },

    upload: function() {
        var files = $(this.el).find("input[type='file']")[0].files;
        var self = this;
        var progress = $(this.el).find('.progress')

        if (files.length > 0) {
            progress.show();

            $.getJSON('/service/ref/import/upload_url/'+this.model.get('root'), function(urls){
                var xhr = new XMLHttpRequest();
 
                xhr.upload.addEventListener('progress', function(evt){
                    var percent = evt.loaded/evt.total*100;
                    progress.find('.bar').css({ 'with': parseInt(percent)+'%' });
                }, false);

                xhr.onreadystatechange = function(){
                    if (xhr.readyState === 4) {
                        $('#progress').hide();
                        
                        console.log('uploaded');

                        self.model.fetch();
                    }
                }
                
                xhr.open('POST', urls[0], true);
               
                if (window.FormData) {
                    var f = new FormData();
                    for (var i=0; i < files.length; i++) {
                        f.append('file_'+i, files[i]);
                    }
                    
                    xhr.send(f);
                } else {
                    var boundary = '------multipartformboundary' + (new Date).getTime();
                    var dashdash = '--';
                    var crlf     = '\r\n';

                    /* Build RFC2388 string. */
                    var builder = '';

                    for (var i=0; i< files.length; i++) {
                        builder += dashdash;
                        builder += boundary;
                        builder += crlf;

                        builder += 'Content-Disposition: form-data; name="file_'+i+'"';
                        builder += '; filename="' + files[i].fileName + '"';
                        builder += crlf;

                        builder += 'Content-Type: '+files[i].type;
                        builder += crlf;
                        builder += crlf;

                        /* Append binary data. */
                        builder += files[i].getAsBinary();
                        builder += crlf;
                    }

                    /* Write boundary. */
                    builder += dashdash;
                    builder += boundary;
                    builder += dashdash;
                    builder += crlf;

                    
                    xhr.setRequestHeader('content-type', 'multipart/form-data; boundary=' + boundary);
                    xhr.sendAsBinary(builder);
                }
            });
        }
    }
});

var tree = $('.tree');

ref_form = new RefForm({ el: tree.find('div.form'), model: current_ref });
ref_tree = new TreeView({ el: tree.find('.wrapper')[0] }).render();

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

