var LinksFieldView = FieldView.extend({
    template: _.template([
        "<% for (i in value) { %>",
        "<a href='#edit/<%=value[i][0]%>'><%=value[i][1]%></a>",
        "<% } %>"
        ].join('\n'))
});

