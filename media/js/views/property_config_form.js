var PropertyConfigForm = BaseForm.extend({
    tagName: "form",
    className: "form",

    initialize: function(opts){
        var self = this;
        _.bindAll(this, "property_changed");

        this.config_fields = new PropertyCollection();
        this.parent_view = opts.parent_view;  

        var values = _.extend({}, this.model.get('config'));

        if (opts.config_fields) {
            _.each(opts.config_fields, function(opt){
                self.config_fields.add(new Property(_.extend(opt, {locked:true, value: values[opt.id]||""})));
            });
        }
        
        this.config_fields.bind("change", this.property_changed);
    },

    render: function(){
        var self = this;
        var container = this.make("ol");

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
        this.parent_view.options['parent_view'].render();
    }
});

