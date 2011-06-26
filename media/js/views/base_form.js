var BaseForm = Backbone.View.extend({
    tag_name: "form",

    getTag: function(prop) {
        var tagTypes = {
            'static': StaticFieldView,
            'text': TextFieldView,
            'links': LinksFieldView,
            'select': SelectFieldView,
            'ref': RefFieldView
        };
       
        var tag = tagTypes[prop.get('type')];
        if (!tag)
            tag = StaticFieldView;

        return new tag({model: prop, parent_view: this});
    }
});


