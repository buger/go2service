steal("https://ajax.googleapis.com/ajax/libs/jquery/1.5.1/jquery.min.js",
      "https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.11/jquery-ui.min.js",
      "base/jquery-ui-i18n.min",
      "base/jquery-ui-timepicker-addon",
      "base/jquery-ui-timepicker-i18n",
      "base/grid.locale-ru",
      "base/jquery.jqGrid.min",
      "base/init_tables",
      "base/jquery.form",
      "base/store.min",
      "base/underscore-min",
      "base/backbone-min",
      "base/facebox"
      )
.models("import", "property", "ref", "tree_item")
steal("views/base_form",
           "views/property_config_form",
           "views/ref_form",           
           "views/import",
           "views/export",
       "views/field",
           "views/fields/links_field",
           "views/fields/ref_field",
           "views/fields/select_field",
           "views/fields/static",
           "views/fields/text_field",
        "views/tree",
        "views/tree_item"
)
.then(function(){
    steal("base/reference",
          "controllers/ref");

    Backbone.emulateHTTP = true;
    $('input.datetime').datetimepicker({showWeek: true});
});
