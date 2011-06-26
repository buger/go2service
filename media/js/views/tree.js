var TreeView = Backbone.View.extend({
    className: "wrapper",

    initialize: function() {
        _.bindAll(this, "render"); 
    },    

    render: function() {
        for (var i=0; i<10; i++){
            this.el.innerHTML += "<div class='level_"+i+" level'></div>";
        }

        if (this.options['root']) {
            var model = new TreeItemModel({ id: this.options['root'], name:'Корень', group: true, import_id: this.options['import_id']});
            
            $(this.el).addClass('without-editing');
        } else {
            var model = new TreeItemModel({ id: 'root', name:'Корень', group: true});
        }
        
        $(this.el).animate({ scrollLeft: 200 }, 0);

        var view = new TreeItemView({ model: model, className: "node-root", scroll: false});
        
        this.$('.level_0').html(view.render().el); 

        this.el.view = this;

        return this.el;        
    },

    levels_template: _.template([
        '<% _.each(items, function(item){ %>',
        '<a href="javascript:;" data-ref-id="<%=item.id%>"><%= item.get("name") %></a><span>▸</span>',
        '<% }); %>'
    ].join('')),

    updateLevelsHeader: function(){
        var self = this;
        var container = $(this.el).parent().find('.levels_header');
        var opened_divs = this.$('div.opened:visible');
        var opened = _.map(opened_divs, function(el){ return el.view.model });

        this.$('div.active').removeClass('active');

        $(_.last(opened_divs)).addClass('active');

        container.html(this.levels_template({ items: opened }));

        container.find('span:last').hide();
        container.find('a:last').css({ 'font-weight': 'bold' });

        container.find('a').bind('click', function(evt) {            
            var id = $(this).data('ref-id');

            var tree_item = container.parent().find('.node-'+id+':visible');

            if (tree_item.get(0)) {
                var view = tree_item.get(0).view;
                $(self.el).animate({ scrollLeft: (view.level) * 200});
                
                view.edit();
                self.updateLevelsHeader();
            }
        });
    },
    
    action_bar_template: _.template([
        "<a class='config button'>▾</a>",
        "<div class='panel' style='display:none'>",
            "<a role='add'>Создать запись</a>",
            "<a role='import'>Импорт</a>",
        "</div>"
    ].join('')),

    destroy: function(id) {
        $('.node-'+id).each(function(idx, el){
            el.view.remove();
        });
    }
});

// Global listener to close opened panel
$(document).click(function(evt){
    $('.item .panel:visible').hide();
    $('.item .config.opened').removeClass('opened');
});

