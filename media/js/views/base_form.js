var BaseForm = Backbone.View.extend({
    tag_name: "form",
    
    editable_field_types: {
        'text': 'Текстовое поле', 
        'select': 'Справочник',
        'checkbox': 'Флаг'
    },

    fieldTypesSelect: function(default_value){
        var self = this;

        var field_type = this.make("select", { class:"field_type" });        

        _(this.editable_field_types).each(function(value, key){
            var option_attrs = { value: key };

            if (default_value && key == default_value) {
                option_attrs['selected'] = 'selected';
            }

            field_type.appendChild(self.make("option", option_attrs, value));
        });

        return field_type;
    },

    getTag: function(prop) {
        var tagTypes = {
            'static': StaticFieldView,
            'text': TextFieldView,
            'links': LinksFieldView,
            'select': SelectFieldView,
            'ref': RefFieldView,
            'checkbox': CheckboxFieldView
        };
       
        var tag = tagTypes[prop.get('type')];
        if (!tag)
            tag = StaticFieldView;

        return new tag({model: prop, parent_view: this});
    }
});


