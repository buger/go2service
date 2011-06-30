var tree_item_tmpl = ["<div class='item'>",
                        "<a class='config button'>▾</a>",
                        "<div class='panel' style='display:none'>",
                            "<a href='#add/<%=id%>'>Создать запись</a>",
                            "<a href='#import/<%=id%>'>Импорт</a>",
							"<a href='#export/<%=id%>'>Экспорт</a>",
                        "</div>",
                        "<a class='name'><%= name || 'Без названия' %></a>",
                     "</div>"].join('');


var TreeItemView = Backbone.View.extend({

    tagName: "div",

    events: {
        "click .name:first": "edit",
        "click .config": "open_panel"
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

        var opened_items = store.get('tree-state');

  //      if (opened_items && _.include(opened_items, this.model.id))
//            $(this.el).addClass('opened');

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

        if (!this.model.get('group')) {
            container.empty();
            
            if (this.scroll != false) {
                $(self.el).closest('.wrapper').animate({ scrollLeft: (self.level-1)*200});
            }
        } else {
            if (!container[0]) {
                container = $("<div class='level level_"+(this.level+1)+"'></div>");
                $(this.el).closest('.wrapper').append(container);
                container = $(this.el).parents('.wrapper').find('.level_'+(this.level+1));
            }

            container.empty();

            this.model.get('children').each(function(el){
                var view = new TreeItemView({ model: el, level: self.level+1});

                container.append(view.render().el);
            });

            $(self.el).closest('.wrapper')[0].view.updateLevelsHeader();


            if (this.scroll != false) {
                $(self.el).closest('.wrapper').animate({ scrollLeft: (self.level)*200});
            }
        }

        this.scroll = true;
    },
    
    open_panel: function(evt){
        this.$('.config').toggleClass('opened');
        this.$('.panel').toggle();

        evt.stopPropagation();
    },

    open: function(render) {
        var self = this;

        $(this.el).parents('.level').find('div.opened').removeClass('opened');
        $(this.el).parents('.level').nextAll().find('div.opened').removeClass('opened');

        $(this.el).addClass('opened');        

        if (!this.model.get('loaded')) {
            $(this.el).parents('.level').next().html('Загрузка...');
            
            this.model.fetch({silent: true, success: function(){ self.renderChildren()} });
        } else {
            setTimeout(function(){
                self.renderChildren();
            }, 0);
        }  
        
        try {
            $(this.el).parents('.wrapper').get(0).view.updateLevelsHeader();
        } catch(e) {}      
    },

    edit: function() {
        var self = this;

        if ($(this.el).closest('.without-editing').length == 0) {
            var opened_divs = $(this.el).closest('.wrapper').find('div.opened:visible');
            var opened = _.map(opened_divs, function(el){ return el.view.model });
            store.set('tree-state', _.map(opened, function(item){ return item.id }));
            
            document.location.hash = "#edit/"+self.model.id;
        }
        
        this.open();
    }
});

