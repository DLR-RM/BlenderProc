from docutils.parsers.rst import Directive
from docutils import nodes
import pdb
from collections import defaultdict
from sphinx import addnodes

class classlist(nodes.General, nodes.Element):
    pass


class ClasslistDirective(Directive):

    def run(self):
        return [classlist('')]

def generate_classlist(app, fromdocname):
    env = app.builder.env
    container = nodes.compound(classes=['toctree-wrapper'])#addnodes.compact_paragraph('', '', classes=['toctree-wrapper'])
    py = env.get_domain('py')
    classes = [_ for _ in py.get_objects() if _[2] == 'class']


    n = defaultdict(list)
    for e in classes:
        newnode = nodes.reference('', '')
        name = e[0].split(".")[-1]
        #print(e)
        innernode = nodes.Text(name)
        newnode['refdocname'] = e[3]
        newnode['refuri'] = app.builder.get_relative_uri(
            fromdocname, e[3])
        newnode['refuri'] += '#' + e[4]
        newnode.append(innernode)

        para = addnodes.compact_paragraph('', '', newnode)
        item = nodes.list_item('', para)

        module = e[0].split(".")[1]
        n[module].append(item)

    for module in sorted(n.keys()):
        container += nodes.caption(module, '', *[nodes.Text(module.capitalize())])

        toc = nodes.bullet_list()
        for class_obj in n[module]:
            toc += class_obj
        container += toc
    return container

def process_classlist(app, doctree, fromdocname):
    container = generate_classlist(app, fromdocname)

    ctx = app.env.config['html_context']
    ctx['classlist'] = container
    for node in doctree.traverse(classlist):
        node.replace_self([container])
        continue


def add_classlist_handler(app):
    def _print_classlist(**kwargs):
        ctx = app.env.config['html_context']
        return app.builder.render_partial(ctx['classlist'])['fragment']

    ctx = app.env.config['html_context']
    if 'print_classlist' not in ctx:
        ctx['print_classlist'] = _print_classlist

def html_page_context(app, pagename, templatename, context, doctree):
    def make_toctree(collapse=True, maxdepth=-1, includehidden=True, titles_only=False):
        fulltoc = generate_classlist(app, "")
        rendered_toc = app.builder.render_partial(fulltoc)['fragment']
        return rendered_toc

    context['toctree'] = make_toctree

def setup(app):
    app.add_node(classlist)
    app.add_directive('classlist', ClasslistDirective)
    app.connect('doctree-resolved', process_classlist)
    app.connect('builder-inited', add_classlist_handler)
    app.connect('html-page-context', html_page_context)
