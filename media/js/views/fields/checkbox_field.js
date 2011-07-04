var CheckboxFieldView = FieldView.extend({
    template: _.template("<input name='<%=name%>' value='1' type='checkbox' <% if (value) { %>checked='checked'<% } %>  />"),

    initialize: function(opts) {
        this._super('initialize', opts);
    }
});
