var ImportForm = Backbone.View.extend({
    tagName: 'div',
    className: 'import-form',    

    events: {    
        "change input[type='file']": "upload",
        "click .new-import": "new_import",
        "click .complete-import": "complete_import",
        "click .next-step": "next_step"
    },

    templates: {
        'init': _.template([
            "<label>Выберите CSV файл для импорта</label>",
            "<input type='file' />",
            "<div class='progress' style='display:none'><div class='bar'></div></div>"
        ].join('')),

        'processing': _.template([
            "<h3>Обработка записей</h3>",
            "<div><%=message%></div>",
            "<div class='progress'><div class='bar' style='width:<%=count/all_count*100%>%'></div></div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('')),

        'error': _.template([
            "<h3>Ошибка импорта</h3>",
            "<div><%=message%></div>",
            "<div class='new-import'>Начать новый импорт</div>"
        ].join('')),

        'merging': _.template([
            "<h3>Анализ загруженных данных</h3>",
            "<div><%=message%></div>",
            "<div class='progress'><div class='bar' style='width:<%=count/all_count*100%>%'></div></div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('')),

        'preview': _.template([
            "<h3>Предварительный просмотр",
                "<div class='complete-import'>Завершить импорт</div>",
            "</h3>",
            "<div class='legend'>",
                "<div class='new'>Новые</div>",
                "<div class='changed'>Измененные</div>",
                "<div class='unchanged'>Неизмененные</div>",
            "</div>",
            "<div class='tree'>",
                "<div class='left'>",
                    "<div class='levels_header'></div>",
                    "<div class='wrapper'></div>",
                "</div>",
            "</div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('')),

        'finalizing': _.template([
            "<h3>Обновление справочника</h3>",
            "<div class='progress'><div class='bar' style='width:<%=count/all_count*100%>%'></div></div>",
            "<div class='new-import'>Остановить и начать новый импорт</div>"
        ].join('')),
    },
    
    initialize: function(){
        _.bindAll(this, "render", "update_state");
        this.model.fetch();
        this.model.bind('change', this.render);
        this.model.bind('change', this.update_state);        
    },
    
    update_state: function(){
        var self = this;
        var state = this.model.get('state')

        if (state == 'processing' || state == 'merging' || state == 'finalizing') {
            clearInterval(this.refresh_timer);

            this.refresh_timer = setInterval(function(){
                self.model.fetch();
            }, 2000);
        } else {
            clearInterval(this.refresh_timer);
        }

        if (state == 'merging' && this.model.get('count') >= this.model.get('all_count')) {
            $.getJSON("/service/ref/import/"+this.model.id+"/set_state/preview", function(){});
            this.model.set({ state: 'preview' });
            
            clearInterval(this.refresh_timer);
        }
        
        if (state == 'finalizing' && this.model.get('count') >= this.model.get('all_count')) {
            clearInterval(this.refresh_timer);
            $.facebox.close();
            ref_workspace.saveLocation("");
            update_tree_item(this.model.get('root'));
            
            setTimeout(function(){
                self.model.destroy();
            }, 1000);
        }
    },

    render: function(){
        var template = this.templates[this.model.get('state')];
        var html = template(this.model.toJSON());        

        $(this.el).html(this.make("div", {className:this.model.get('state')}, html));

        $.facebox($(this.el));

        if (this.model.get('state') == 'preview') {
            new TreeView({ 
                el: $(this.el).find('.wrapper')[0], 
                root: this.model.get('root'), 
                import_id: this.model.id
            }).render();
        }

        this.delegateEvents();
    },
    
    next_step: function(){
        $.getJSON("/service/ref/import/"+this.model.id+"/set_state/preview", function(){});
        this.model.set({ state: 'preview' });
        
        clearInterval(this.refresh_timer);
    },

    new_import: function(){
        var self = this;
        var root = this.model.get('root');

        this.model.destroy({success: function(model, response){
            self.model.set({'root': root }, { silent: true });            
            self.model.fetch();
        }});
    },

    complete_import: function(){
        $.getJSON("/service/ref/import/"+this.model.id+"/set_state/finalizing", function(){});
        this.model.set({ state: 'finalizing', count: 0 });        
    },

    upload: function() {
        var files = $(this.el).find("input[type='file']")[0].files;
        var self = this;
        var progress = $(this.el).find('.progress')

        if (files.length > 0) {
            progress.show();

            $.getJSON('/service/ref/import/upload_url/'+this.model.get('root'), function(urls){
                var xhr = new XMLHttpRequest();
 
                xhr.upload.addEventListener('progress', function(evt){
                    var percent = evt.loaded/evt.total*100;
                    progress.find('.bar').css({ 'with': parseInt(percent)+'%' });
                }, false);

                xhr.onreadystatechange = function(){
                    if (xhr.readyState === 4) {
                        $('#progress').hide();
                        
                        console.log('uploaded');

                        self.model.fetch();
                    }
                }
                
                xhr.open('POST', urls[0], true);
               
                if (window.FormData) {
                    var f = new FormData();
                    for (var i=0; i < files.length; i++) {
                        f.append('file_'+i, files[i]);
                    }
                    
                    xhr.send(f);
                } else {
                    var boundary = '------multipartformboundary' + (new Date).getTime();
                    var dashdash = '--';
                    var crlf     = '\r\n';

                    /* Build RFC2388 string. */
                    var builder = '';

                    for (var i=0; i< files.length; i++) {
                        builder += dashdash;
                        builder += boundary;
                        builder += crlf;

                        builder += 'Content-Disposition: form-data; name="file_'+i+'"';
                        builder += '; filename="' + files[i].fileName + '"';
                        builder += crlf;

                        builder += 'Content-Type: '+files[i].type;
                        builder += crlf;
                        builder += crlf;

                        /* Append binary data. */
                        builder += files[i].getAsBinary();
                        builder += crlf;
                    }

                    /* Write boundary. */
                    builder += dashdash;
                    builder += boundary;
                    builder += dashdash;
                    builder += crlf;

                    
                    xhr.setRequestHeader('content-type', 'multipart/form-data; boundary=' + boundary);
                    xhr.sendAsBinary(builder);
                }
            });
        }
    }
});



