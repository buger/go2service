var RefFieldView = FieldView.extend({
    ref_item: new RefModel(),    

    events: {    
        "click input[type='button']": "select_ref"
    },    

    template: _.template([
        "<%=view%><input type='button' value='Выберите справочник'/>"
    ].join('')),   

    window_template: _.template([
        "<input type='button' value='Выбрать и закрыть окно' disabled />",
        "<br/>",
        "<div class='tree'>",
            "<div class='left'>",
                "<div class='levels_header'></div>",
                "<div class='wrapper'></div>",
            "</div>",
        "</div>"
    ].join('')),

    initialize: function(opts){
        var self = this;

        if (this.model.get('value')) {
            this.model.set({ view: 'Загрузка...' }, {silent: true});
            
            this.ref_item.set({id: this.model.get('value')});

            this.ref_item.fetch({
                success: function(){
                    self.model.set({ view: self.ref_item.get('name') }, {silent:true});       
                    self.render();
                }
            });
        } else {
            this.model.set({ view: 'Не выбрано' }, {silent: true});
        }

        this._super('initialize', opts);
    },    

    select_ref: function(){
        var self = this;
        var html = this.window_template();
        var container = $("<div/>").html(html);

        var tree = new TreeView({ root:'root', import_id:''}).render();
        container.find('.left').append(tree);

        $(tree).bind('click', function(){
            container.find('input[type="button"]').removeAttr('disabled');
        });
        
        container.find('input[type="button"]').bind('click', function(){
            var selected = container.find('div.active')[0].view.model;            

            var config = _.extend({}, self.parent_view.model.get('config'));
            config[self.model.get('id')] = selected.id;

            self.parent_view.model.set({'config': config});

            self.model.change();

            $.facebox.close();
        });

        $.facebox(container);

        $(document).bind('afterClose.facebox', function(){
            $(document).unbind('afterClose.facebox');
            self.parent_view.configure_field();
        });
    }
});

