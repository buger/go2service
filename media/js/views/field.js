var FieldView = Backbone.View.extend({
    tagName: 'li',

    events: {
        "click .delete_field": "remove_field",
        "click .configure_field": "configure_field",
        "change label input": "change_label",
        "change span.field input": "change_value",
        "change span.field select": "change_value"
    },

    initialize: function(opts) {
        if (opts)
            this.parent_view = opts.parent_view;
    },

    render: function() {
        $(this.el).empty();

        if (this.model.get('locked')) {
            var label_text = this.model.get('label') || ref_form_names[this.model.id];
        } else {
            var label_text = this.make("input", {value: this.model.get('label'), type: 'text'});
        }
        
        var label = this.make("label", { 'for': this.model.id }, label_text);
        
        var field_container = this.make("span", { 'class': 'field' }, this.template(this.model.toJSON()));
        $(this.el).append(label)
            .append(field_container);
        
        if (!this.model.get('locked')) {
            var delete_link = this.make("a", {'class': 'delete_field'}, "✕");
            $(this.el).append(delete_link);
            
            var configure_link = this.make("a", {'class': 'configure_field'}, "C");
            $(this.el).append(configure_link);
        } else {
            if (this.model.get('inherited_from')) {
                var info = this.make('span', {'class': 'info', title:"Унаследовано от "+this.model.get('inherited_from')}, 'i');
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
    
    config_fields: [],

    configure_field: function(){
        var html = new PropertyConfigForm({ model: this.model, config_fields: this.config_fields, parent_view: this }).render();

        $.facebox(html);
    },

    change_value: function(){
        var field = this.$('.field input, .field select');

        if (field.attr('type') == 'checkbox') {
            var value = field.attr('checked');
        } else {
            var value = field.val();
        }

        this.model.set({ 'value': value });
    },

    change_label: function(){
        this.model.set({ 'label': this.$('label input').val() });
    }
});

