# -*- coding: utf-8 -*-
from __future__ import with_statement   
from handlers.service import *
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers



#обработка экспорта

from lib.models import *
from lib.unicode_csv import *

#унаследованные имена полей
def parent_label(ref):
    data = []
    for parent in ref.ancestors:
        parent = db.get(parent)            
        for prop in parent.props:
            data.append(prop['label'])
    return  data

#унаследованные свойства            
def parent_props(ref):
    data = []
    for parent in ref.ancestors:
        parent = db.get(parent)            
        for prop in parent.props:
            data.append(prop)
    return data

            
#получить список  имен всех возможных полей объектов       
def get_all_label(ref):           
    def func_get_all_label(ref, data):
        for prop in ref.props:
            data.append(prop['label'])

        key = ref.key()    
        items = ref.__class__.all().filter("parents =", key)    
        for item in items:
            func_get_all_label(item,data)
        
    
    data = parent_label(ref)
    func_get_all_label(ref, data)
    return list(set(data))
    
    
#запись объекта в формате csv        
def writerow(ref, writer, cols, p_props, first):
    row = []
    row.append(ref.name)
    
    if  first: #записываем родителей
        row.append(""); #если корневой элемент
        first = False
    else:
        row.append('|'.join([db.get(parent).name for parent in ref.parents]))                                 
    
    props = ref.props    
    
    for col in cols:            
        find_prop = filter(lambda r: r.get('label') == col, props)
        if find_prop:
            prop = find_prop[0]
            row.append('*')                                                
            row.append(prop['type'])
            try:
                row.append(getattr(ref, str(prop['id'])))
            except AttributeError:
                row.append('')               
        else:
            #p_props = parent_props(ref)
            find_prop = filter(lambda r: r.get('label') == col, p_props)
            if find_prop:
                prop = find_prop[0]
                row.append('')                                                
                row.append(prop['type'])
                try:
                    row.append(getattr(ref, str(prop['id'])))
                except AttributeError:
                    row.append('')               
            else:
                row.append('')                                                
                row.append('')
                row.append('')

                                   
    writer.writerow(row)
    #print row

    #рекурсивный спуск по дереву
    key = ref.key()    
    items = ref.__class__.all().filter("parents =", key)        
    for item in items:
        writerow(item, writer, cols, props + p_props, first)

 
            
    
#непосредственно обработка экспорта
    
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, key):    
        file_name = files.blobstore.create(mime_type='text/csv')
                
        ref = Ref.get(db.Key(key))        
    
        cols = get_all_label(ref)        

        header = ['Name', 'Parents']
        for col in cols:
            header.append('%s - Owner' % col)
            header.append('%s - Type' % col)
            header.append('%s - Value' % col)

        with files.open(file_name, 'a') as f:
            writer = UnicodeWriter(f, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
            writer.writerow(header)
            p_props = parent_props(ref)
            first = True
            writerow(ref, writer, cols, p_props, first)
            

        # Finalize the file. Do this before attempting to read it.
        files.finalize(file_name)
        # Get the file's blob key
        
        blob_key = files.blobstore.get_blob_key(file_name)            
        self.response.headers['Content-Disposition'] = 'attachment; filename=%s_.csv' % ref.name
        self.send_blob(blob_key)


#================================================

route('/service/ref/download/:key', ServeHandler)