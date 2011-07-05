//============================== by fox  ===========================================

var ExportForm = Backbone.View.extend({
    tagName: 'div',
    className: 'import-form',    
    
    events: {    
    },
    
    templates: {
        'init': _.template([
            "<div id = 'my'><a id = 'mya' href = '/service/ref/download/<%=root%>'>начать экспорт</a></div>",
            "<div class='progress' style='display:none'><div class='bar'></div></div>"
        ].join(''))	
    },

    initialize: function(){
       this.model.fetch();
       this.render();
       console.log('init');
//	    $.getJSON('/service/ref/export/upload_url/'+this.model.get('root'), function(urls){			
//			$('#mya').attr('href', urls[0]);
//            $('#mya').html('download');
//			}
//		)	   
       console.log('ready');
    },


    download: function () {
        alert('done');
    },


    render: function(){
        var template = this.templates['init'];
        //alert(JSON.stringify(this.model));
        var html = template(this.model.toJSON());        

        $(this.el).html(this.make("div", {className:this.model.get('state')}, html));
        $.facebox($(this.el));

        //this.refresh_timer = setInterval(function(){                
        //$('#my').
        //		$('#my').html('bla')
        //}, 5000);

        this.delegateEvents();
    },	
})