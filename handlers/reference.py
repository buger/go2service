# -*- coding: utf-8 -*-
from handlers.service import *

import simplejson as json
import time

class RefIndex(ServiceHandler):
    def get(self):
        self.render_template("service/reference.html")

route('/service/ref', RefIndex)


class RefTree(ServiceHandler):
    def get(self, key):
        if not key:
            return self.error(404)

        import_id = self.request.get('import_id')

        if key == 'root':
            items = Ref.all().filter("root =", True)
        else:
            if import_id:
                items = RefImportItem.all().filter("ref_import =", db.Key(import_id)).filter("parent_name =", key)
            else:
                key = db.Key(key)
                items = eval(key.kind()).all().filter("parents =", key)

        items = [item.toJSON() for item in items]

        self.render_json({ 'children': items })

    def post(self, key):
        model = json.loads(self.request.body)

        ref = Ref(name = model["name"])

        if not model["parents"]:
            ref.root = True
        else:
            parent = Ref.get(db.Key(model["parents"][0][0]))
            if not parent.group:
                parent.group = True
                parent.put()

            ancestors = parent.ancestors
            ancestors.append(parent.key())

            ref.ancestors = parent.ancestors
            ref.parents = [parent.key()]


        ref.put()

        self.render_json(ref.toJSON())

route('/service/ref/tree/:key', RefTree)


class RefGet(ServiceHandler):
    def new_or_existing(self, key, model = None):
        if key == 'new':
            ref = Ref()

            if model:
                if model['parents']:
                    parent = Ref.get(db.Key(model['parents'][0][0]))
                else:
                    ref.root = True
                    parent = None
            else:
                if self.request.get('parent') != 'root':
                    parent = Ref.get(db.Key(self.request.get('parent')))
                else:
                    parent = None

            if parent:
                if not parent.group:
                    parent.group = True
                    parent.put()

                ref.parents.append(parent.key())
                ref.ancestors = parent.ancestors
                ref.ancestors.append(parent.key())
        else:
            ref = Ref.get(db.Key(key))

        return ref


    def get(self, key):
        if not key:
            return self.error(404)

        ref = self.new_or_existing(key)

        self.render_json(ref.toJSON(True))

    def post(self, key):
        if self.request.headers['X-Http-Method-Override'] == "DELETE":
            db.delete(db.Key(key))

            self.render_json({'success': True})
        else:
            model = json.loads(self.request.body)

            ref = self.new_or_existing(key, model)

            ref.name = model['name']

            old_props = ref.props

            ref.props = []

            for prop in model['props']:

                if prop['type'] == 'select':
                    try:
                        old_prop = filter(lambda p: p['id'] == prop['id'], old_props)[0]
                    except:
                        old_prop = {}

                    if 'config' in old_prop and 'act_as_parent' in old_prop['config'] and old_prop['config']['act_as_parent']:
                        value = getattr(ref, str(old_prop['id']))

                        if value != '':
                            ref.parents.remove(db.Key(value))
                            ref.ancestors.remove(db.Key(value))

                    if 'config' in prop and 'act_as_parent' in prop['config'] and prop['config']['act_as_parent']:
                        if prop['value'] != '':
                            parent = db.get(db.Key(prop['value']))

                            if not parent.group:
                                parent.group = True
                                parent.put()

                            ref.parents.append(parent.key())
                            ref.ancestors.append(parent.key())

                if u'locked' not in prop:
                    ref.props.append(prop)

                if prop['type'] != u'static' and prop['type'] != u'links':
                    setattr(ref, str(prop['id']), prop['value'])

                del prop['value']

            if not ref.is_saved():
                counter = CachedCounter('Ref')
                ref.num_id = counter.incr()

            ref.put()

            self.render_json(ref.toJSON(True))

route('/service/ref/:key', RefGet)
