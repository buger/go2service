var PropertyConfigForm = BaseForm.extend({
    tagName: "form",
    className: "form",

    initialize: function(opts){
        var self = this;
        _.bindAll(this, "property_changed");

        this.config_fields = new PropertyCollection();
        this.parent_view = opts.parent_view;  

        var values = _.extend({}, this.model.get('config'));

        if (this.parent_view && this.parent_view.config_fields) {
            _.each(this.parent_view.config_fields, function(opt){
                self.config_fields.add(new Property(_.extend(opt, {locked:true, value: values[opt.id]||""})));
            });
        }
        
        this.config_fields.bind("change", this.property_changed);
    },

    render: function(){
        var self = this;
        var container = this.make("ol");

        var field_type = this.fieldTypesSelect(this.model.get('type'));
        container.appendChild(this.make("li", {}, field_type));

        $(field_type).bind('change', function(){
            self.model.set({ 'type': $(this).val() });
            self.parent_view.parent_view.render();            
        
            $.facebox.close();
        });

        this.config_fields.each(function(prop) {
            var tag = self.getTag(prop);
            tag.parent_view = self.parent_view;  
            
            container.appendChild(tag.render().el);
        });
        
        $(this.el).empty()
            .append(container);

        return this.el;
    },

    property_changed: function(prop){
        var config = _.extend({}, this.parent_view.model.get('config'));
        config[prop.get('id')] = prop.get('value');

        this.parent_view.model.set({'config': config});
        this.parent_view.model.change();

        this.parent_view.options['parent_view'].render();

        console.log('prop changed');
    }
});

