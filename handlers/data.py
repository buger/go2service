# -*- coding: utf-8 -*-
from __future__ import with_statement   
from handlers.service import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import taskqueue

from google.appengine.api import files

import simplejson as json
import time
import hashlib


class RefImportUploadUrl(AppHandler):
    def get(self, key):
        self.render_json([blobstore.create_upload_url('/service/ref/import/upload/'+key)])

route('/service/ref/import/upload_url/:key', RefImportUploadUrl)


#=========== by fox ==================================================
#обработка экспорта

from lib.models import *
from lib.unicode_csv import *


#все возможные унаследованные имена поля
def parent_label(ref, data):
    for parent in ref.ancestors:
        parent = db.get(parent)            
        for prop in parent.props:
            data.append(prop['label'])

#все возможные унаследованные свойства            
def parent_props(ref):
    data = []
    for parent in ref.ancestors:
        parent = db.get(parent)            
        for prop in parent.props:
            data.append(prop)
    return data

            
#все унаследованные, собственные и дочерние имена полей            
def child_label(ref, data):           
    def func_child_label(ref, data):
        for prop in ref.props:
            data.append(prop['label'])

        key = ref.key()    
        items = eval(ref.kind()).all().filter("parents =", key)    
        for item in items:
            func_child_label(item,data)
        
    
    parent_label(ref, data)
    func_child_label(ref, data)
    data = list(set(data))

#запись объекта в формате csv        
def writerow(ref, writer, cols):
    row = []
    row.append(ref.name)
    if ref.parents:
        row.append(db.get(ref.parents[0]).name) #todo check parents and many parents
    else:
        row.append('')
    props = ref.props
    p_props = parent_props(ref)
    for col in cols:            
        find_prop = filter(lambda r: r.get('label') == col, props)
        if len(find_prop) > 0:
            prop = find_prop[0]
            row.append('*')                                                
            row.append(prop['type'])
            row.append(getattr(ref, str(prop['id'])))
        else:
            find_prop = filter(lambda r: r.get('label') == col, p_props)
            if len(find_prop) > 0:
                prop = find_prop[0]
                row.append('')                                                
                row.append(prop['type'])
                row.append(getattr(ref, str(prop['id'])))
            else:
                row.append('')                                                
                row.append('')
                row.append('')
                                   
    writer.writerow(row)
    #print row

    #рекурсивный спуск по дереву
    key = ref.key()    
    items = eval(ref.kind()).all().filter("parents =", key)    
    for item in items:
        writerow(item, writer, cols)

 
            
    
#непосредственно обработка экспорта
    
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, key):    
        file_name = files.blobstore.create(mime_type='text/csv')
                
        ref = Ref.get(db.Key(key))        
        cols = []
        child_label(ref, cols)        

        header = ['Name', 'Parents']
        for col in cols:
            header.append('%s - Owner' % col)
            header.append('%s - Type' % col)
            header.append('%s - Value' % col)

        with files.open(file_name, 'a') as f:
            writer = UnicodeWriter(f, delimiter = ',', quoting = csv.QUOTE_ALL)    
            writer.writerow(header)
            writerow(ref, writer, cols)
            

        # Finalize the file. Do this before attempting to read it.
        files.finalize(file_name)
        # Get the file's blob key
        
        blob_key = files.blobstore.get_blob_key(file_name)                       
        self.send_blob(blob_key)

route('/service/ref/download/:key', ServeHandler)
#================================================

class ParseImportHeaderError(StandardError):
    pass


import sys
import csv
import re

rQUOTE = re.compile("\"")
rCOL_NAME = re.compile(u"[—-].*")

class RefImportUpload(blobstore_handlers.BlobstoreUploadHandler):
    def read_header(self, ref, reader):
        line = reader.readline()

        cols = line.split(',')

        cols = [rQUOTE.sub('', col).decode('utf-8') for col in cols]

        required_columns = [u"Name",u"Parents"]

        for col in required_columns:
            if col not in cols:
                ref.message = u"Не найдены обязательные колонки Name и Parents"
                raise ParseImportHeaderError

        header = [
            {'label': 'Name', 'id': 'name' },
            {'label': 'Parents', 'id': 'parents' }
        ]

        for col in cols:
            if col in required_columns:
                continue

            col_name = rCOL_NAME.sub('', col).strip()

            column = {}

            column_types = [u'Owner', u'Type', u'Value']
            col_type = filter(lambda ct: re.search(ct, col), column_types)

            if len(col_type) > 1:
                ref.message = u"В названии колонки '%s' используется несколько ключевых слов" % col_type[0]
                raise ParseImportHeaderError
            elif len(col_type) == 1:
                column['type'] = col_type[0].lower()
                column['id'] = column['type']
                column['label'] = col_name
            else:
                ref.message = u"Не определен тип колонки %s" % col
                raise ParseImportHeaderError

            header.append(column)

        ref.columns = header


    def post(self, key):
        upload = self.get_uploads()[0]

        ref_import = RefImport(blob_key = str(upload.key()), root = key, state = "processing", all_count = upload.size)
        ref_import.put()

        reader = blobstore.BlobReader(upload.key())

        try:
            self.read_header(ref_import, reader)
            ref_import.incr(reader.tell())
        except ParseImportHeaderError:
            ref_import.state = "error"


        ref_import.put()

        if ref_import.state != "error":
            taskqueue.add(url="/service/ref/import/task/%s/%d" % ( str(ref_import.key()), reader.tell() ), method = 'GET')

        self.error(301)

route('/service/ref/import/upload/:key', RefImportUpload)


class SetImportState(ServiceHandler):
    def get(self, key, state):
        ref_import = RefImport.get(db.Key(key))
        ref_import.state = state
        ref_import.put()

        if state == 'finalizing':
            taskqueue.add(queue_name = "finalizing", url="/service/ref/import/finalize/%s" % str(ref_import.key()), method = 'GET')

route('/service/ref/import/:key/set_state/:state', SetImportState)


class RefImportHandler(AppHandler):
    def get(self, key):
        ref_import = RefImport.all().filter('root =', key).get()

        if ref_import is None:
            self.render_json(model_to_json(RefImport(root = key)))
        else:
            self.render_json(model_to_json(ref_import))

    def post(self, key):
        if self.request.headers['X-Http-Method-Override'] == "DELETE":
            ref_import = RefImport.all(keys_only = True).filter('root =', key).get()
            db.delete(ref_import)

            self.render_json({'success': True})

route('/service/ref/import/:key', RefImportHandler)


IMPORT_BUTCH_SIZE = 10

class ImportMergeTask(ServiceHandler):
    def merge_props(self, import_ref, ref_props):
        changed = False

        for prop in import_ref.props:
            prop_match = filter(lambda p: p.get('label') == prop['label'], ref_props)

            if len(prop_match) != 0:
                prop['real_id'] = prop_match[0]['id']
                prop['locked'] = True

                try:
                    value = getattr(import_ref, str(prop['id']))
                except:
                    value = None

                if value is not None and value != prop_match[0]['value']:
                    changed = True

        return changed


    def get(self, import_key, import_ref_key = None):
        tasks = []
        ref_import = RefImport.get(db.Key(import_key))

        if ref_import is None or ref_import.state != 'merging':
            return False

        try:
            offset = int(self.request.get('offset'))
        except:
            offset = 0

        ref_parent = Ref.get(db.Key(ref_import.root))

        if import_ref_key is None:
            import_refs = RefImportItem.all().filter("ref_import =", ref_import).filter("parent_name =", ref_import.root).fetch(IMPORT_BUTCH_SIZE , offset)
            real_refs = Ref.gql("WHERE parents = :parents AND name = :name")
            import_ref = None
        else:
            import_ref = RefImportItem.get(db.Key(import_ref_key))
            import_refs = RefImportItem.all().filter("ref_import =", ref_import).filter("parent_name =", import_ref.name).fetch(IMPORT_BUTCH_SIZE , offset)

            if len(import_refs) > 0:
                import_ref.group = True
                import_ref.put()


            if import_ref.real_ref:
                real_refs = Ref.gql("WHERE parents = :parents AND name = :name")
            else:
                real_refs = None

        if len(import_refs) == IMPORT_BUTCH_SIZE :
            tasks.append("%s?offset=%d" % (self.request.path, offset+IMPORT_BUTCH_SIZE ))

        for ref in import_refs:
            if real_refs:
                if import_ref_key:
                    real_refs.bind(name = ref.name, parents = import_ref.real_ref.key())
                else:
                    real_refs.bind(name = ref.name, parents = db.Key(ref_import.root))

                match = real_refs.get()
            else:
                match = None

            if import_ref:
                ref.parents = [import_ref.key()]
                ref.ancestors = import_ref.ancestors
                ref.ancestors.append(import_ref.key())

            if match:
                ref.ancestors.append(match.key())
                ref.real_ref = match

                if self.merge_props(ref, match.toJSON(True)['props']):
                    ref.state = "changed"
                else:
                    ref.state = "unchanged"
            else:
                ref.state = "new"
                self.merge_props(ref, ref_parent.toJSON(True)['props'])

            tasks.append("/service/ref/merge/task/%s/%s" % (import_key, str(ref.key())))

        ref_import.incr(len(import_refs))
        ref_import.put()

        db.put(import_refs)

        for task in tasks:
            taskqueue.add(queue_name = "merging", url = task, method = 'GET')

route('/service/ref/merge/task/:import_key/:import_ref_key', ImportMergeTask)
route('/service/ref/merge/task/:import_key', ImportMergeTask)


class ImportFinalizeTask(ServiceHandler):
    def get(self, key, ref_key = None):
        ref_import = RefImport.get(db.Key(key))

        if ref_import is None:
            return False

        try:
            offset = int(self.request.get('offset'))
        except:
            offset = 0

        tasks = []

        if ref_key:
            ref_import_root = RefImportItem.get(db.Key(ref_key))
            ref_root = ref_import_root.real_ref
            ref_import_items = RefImportItem.all().filter("ref_import =", ref_import).filter("parents =", ref_import_root).fetch(IMPORT_BUTCH_SIZE , offset)

            if ref_import_items:
                ref_root.put()
        else:
            ref_root = Ref.get(db.Key(ref_import.root))
            ref_root.group = True
            ref_root.put()

            ref_import_items = RefImportItem.all().filter("ref_import =", ref_import).filter("parent_name =", ref_import.root).fetch(IMPORT_BUTCH_SIZE , offset)

        if len(ref_import_items) == IMPORT_BUTCH_SIZE :
            tasks.append("%s?offset=%d" % (self.request.path, offset+IMPORT_BUTCH_SIZE ))

        root_ancestors = ref_root.ancestors

        for_put = []

        for idx, ref in enumerate(ref_import_items):
            if ref.state == 'unchanged':
                pass
            elif ref.state == 'changed':
                new_ref = ref.real_ref
                new_ref.parents.append(ref_root.key())

                for a in ref_root.ancestors:
                    new_ref.ancestors.append(a)

                new_ref.ancestors.append(ref_root.key())

                new_ref.group = ref.group

                props = ref.toJSON(True)['props']
                props = filter(lambda p: 'imported' in p.keys(), props)

                for prop in props:
                    try:
                        prop_id = str(prop['real_id'])
                    except:
                        prop_id = str(prop['id'])

                    setattr(new_ref, prop_id, prop['value'])

                    if 'locked' not in prop.keys():
                        new_ref.props.append({
                            'id': prop_id,
                            'label': prop['label'],
                            'type': prop['type']
                        })

                new_ref.put()
                ref.real_ref = new_ref
                for_put.append(ref)

            elif ref.state == 'new':
                new_ref = Ref(key_name = ref.key().name())
                new_ref.parents.append(ref_root.key())
                new_ref.ancestors = []

                for a in ref_root.ancestors:
                    new_ref.ancestors.append(a)

                new_ref.ancestors.append(ref_root.key())
                new_ref.name = ref.name
                new_ref.num_id = CachedCounter('Ref').incr()
                new_ref.props = []
                new_ref.group = ref.group

                props = ref.toJSON(True)['props']
                props = filter(lambda p: 'imported' in p.keys(), props)

                for prop in props:
                    try:
                        prop_id = str(prop['real_id'])
                    except:
                        prop_id = str(prop['id'])

                    try:
                        setattr(new_ref, prop_id, prop['value'])
                    except:
                        pass

                    if 'locked' not in prop.keys():
                        new_ref.props.append({
                            'id': prop_id,
                            'label': prop['label'],
                            'type': prop['type']
                        })

                new_ref.put()
                ref.real_ref = new_ref
                for_put.append(ref)

            tasks.append("/service/ref/import/finalize/%s/%s" % (str(ref_import.key()), str(ref.key())))

        ref_import.incr(len(ref_import_items))

        ref_import.put()
        db.put(for_put)

        for task in tasks:
            taskqueue.add(queue_name = "finalizing", url=task, method = 'GET')


route('/service/ref/import/finalize/:import_key', ImportFinalizeTask)
route('/service/ref/import/finalize/:import_key/:ref_key', ImportFinalizeTask)

rCSV = re.compile("\"([^\"]+?)\",?|([^,]+),?|,")

class ImportTask(ServiceHandler):
    def read_ref(self, reader, ref_import):
        line = reader.readline()

        cols = [c[0] or c[1] for c in rCSV.findall(line)]
        cols = [c.decode('utf-8') for c in cols]

        counter = CachedCounter('RefImport')
        name_md5 = hashlib.md5(cols[0].encode('utf-8'))
        ref = RefImportItem(ref_import = ref_import, num_id = counter.incr())

        props = []

        for idx, val in enumerate(cols):
            try:
                col_info = ref_import.columns[idx]
            except IndexError:
                continue

            if u'type' in col_info.keys():
                prop_id = "%d_%d" % (ref_import.key().id(), idx)

                if col_info['type'].lower() == u'value':
                    setattr(ref, prop_id, val)
                elif col_info['type'].lower() == u'owner' and val.strip() == '*':
                    try:
                        value_column = filter(lambda r: r.get('type') == 'value', ref_import.columns)
                        value_column = filter(lambda r: r.get('label') == col_info['label'], value_column)[0]
                        value_column_idx = ref_import.columns.index(value_column)
                    except:
                        ref_import.message = u"Не найдена колонка %s - %s" % (col_info['label'], 'Value')
                        raise StandardError

                    props.append({
                        'label': col_info['label'],
                        'type': 'text',
                        'id': "%d_%d" % (ref_import.key().id(), value_column_idx),
                        'imported': True
                    })
            else:

                if u'parents' == col_info['id'].lower():
                    if val.strip() == '':
                        val = ref_import.root
                        parent_name = val
                    else:
                        parent_name = val

                    setattr(ref, 'parent_name', parent_name)
                else:
                    setattr(ref, col_info['id'], val)

        ref.props = props

        return ref


    def get(self, key, position):
        try:
            rows = int(self.request.get('rows'))
        except:
            rows = 0

        position = int(position)

        ref_import = RefImport.get(db.Key(key))
        reader = blobstore.BlobReader(ref_import.blob_key, position = position)

        for_put = []

        for i in range(10):
            if reader.tell() < reader.blob_info.size:
                try:
                    for_put.append(self.read_ref(reader, ref_import))
                except:
                    ref_import.state = 'error'
                    ref_import.put()
                    return True

                rows += 1
            else:
                ref_import.message = u"Найдено записей: %d" % rows
                ref_import.state = "merging"
                ref_import.all_count = rows
                break

        db.put(for_put)


        if ref_import.state != "merging":
            ref_import.incr(reader.tell()-position)

            taskqueue.add(url="/service/ref/import/task/%s/%d" % ( str(ref_import.key()), reader.tell()), params = {'rows':rows})
        else:
            ref_import.put()
            taskqueue.add(queue_name = "merging", url = "/service/ref/merge/task/%s" % str(ref_import.key()), method = 'GET')



    def post(self, key, position):
        self.get(key, position)

route('/service/ref/import/task/:key/:position', ImportTask)

