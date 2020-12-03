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

def generate_collapsible_classlist(app, fromdocname, classes, container, caption, module_index):

    entries = defaultdict(list)
    prefix = ".".join(classes[0][0].split(".")[:module_index]) + "."
    for e in classes:
        module = e[0].split(".")[module_index]
        entries[module].append(e)

    toc = nodes.bullet_list()
    toc += nodes.caption(caption, '', *[nodes.Text(caption)])
    for module, class_list in entries.items():
        ref = nodes.reference('', '')
        ref['refuri'] = app.builder.get_relative_uri(fromdocname, prefix + module)
        ref.append(nodes.Text(module.capitalize()))
        module_item = nodes.list_item('', addnodes.compact_paragraph('', '', ref), classes=["toctree-l1"])
        if fromdocname.startswith("src." + module):
            module_item["classes"].append('current')
        toc += module_item

        subtree = nodes.bullet_list()
        module_item += subtree

        for e in class_list:
            ref = nodes.reference('', '')
            ref['refdocname'] = e[3]
            ref['refuri'] = app.builder.get_relative_uri(fromdocname, e[3])
            ref['refuri'] += '#' + e[4]
            ref.append(nodes.Text(e[0].split(".")[-1]))
            class_item = nodes.list_item('', addnodes.compact_paragraph('', '', ref), classes=["toctree-l2"])
            if fromdocname.startswith(e[3]):
                class_item['classes'].append('current')
            subtree += class_item

    container += toc

def generate_sidebar(app, fromdocname):
    env = app.builder.env
    container = nodes.compound(classes=['toctree-wrapper'])#addnodes.compact_paragraph('', '', classes=['toctree-wrapper'])
    py = env.get_domain('py')
    classes = [_ for _ in py.get_objects() if _[2] == 'class']

    classes_per_group = {"modules": ([], 1), "provider": ([], 2), "core": ([], 1)}
    for e in classes:
        if e[0].startswith("src.provider."):
            group = "provider"
        elif e[0].startswith("src.main.") or e[0].startswith("src.utility."):
            group = "core"
        else:
            group = "modules"
        classes_per_group[group][0].append(e)

    for key, items in classes_per_group.items():
        generate_collapsible_classlist(app, fromdocname, items[0], container, key.capitalize(), items[1])

    return container

def process_classlist(app, doctree, fromdocname):
    container = generate_sidebar(app, fromdocname)

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
        fulltoc = generate_sidebar(app, "" if "title" not in context else context["title"])
        rendered_toc = app.builder.render_partial(fulltoc)['fragment']
        return rendered_toc

    context['toctree'] = make_toctree

def setup(app):
    app.add_node(classlist)
    app.add_directive('classlist', ClasslistDirective)
    app.connect('doctree-resolved', process_classlist)
    app.connect('builder-inited', add_classlist_handler)
    app.connect('html-page-context', html_page_context)
