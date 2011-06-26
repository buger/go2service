Backbone.View.prototype._super = Backbone.Model.prototype._super = function(funcName){
    return this.constructor.__super__[funcName].apply(this, _.rest(arguments));
}

var ref_form;
var ref_tree;

var current_ref = new RefModel({ props: new PropertyCollection() });

var tree = $('.tree');

ref_form = new RefForm({ el: tree.find('div.form'), model: current_ref });
ref_tree = new TreeView({ el: tree.find('.wrapper')[0] }).render();

