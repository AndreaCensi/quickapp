from __future__ import print_function
from copy import deepcopy

from contracts import contract

from compmake import Promise
from quickapp import CompmakeContext
from quickapp.report_manager import basename_from_key
from reprep import NotExistent, Report, logger


__all__ = ['ReportProxy', 'get_node']


class FigureProxy(object):
    def __init__(self, id_figure, report_proxy):
        self.id_figure = id_figure
        self.report_proxy = report_proxy
        
    @contract(what='str')
    def sub(self, what, **kwargs):
        self.report_proxy.op(rp_figure_sub, id_figure=self.id_figure, what=what, **kwargs)
    
    
class ReportProxy(object):
    
    @contract(context=CompmakeContext)
    def __init__(self, context):
        self.context = context
        self.operations = []
        self.resources = {}
        
    def op(self, function, **kwargs):
        self.operations.append((function, kwargs))
    
    @contract(nid='str')
    def figure(self, nid, **kwargs):
        if nid is None:
            nid = 'Figure'
        self.op(rp_create_figure, id_parent='report', nid=nid, **kwargs)
        return FigureProxy(nid, self)
    
    @contract(child=Promise, nid='str')
    def add_child_with_id(self, child, nid):
        self.op(add_child_with_id, id_parent='report', child=child, nid=nid)
    
    def add_child_from_other(self, url, nid, report_type, strict=True, **report_args):
        part = self.get_part_of(url, report_type, strict=strict, ** report_args)
        
        if nid is None:
            nid = basename_from_key(report_args) + '-' + url.replace('/', '-')  # XXX url chars
            
        self.add_child_with_id(part, nid)
        return nid
 
    @contract(returns=Promise, url=str, report_type=str)
    def get_part_of(self, url, report_type, strict=True, **report_args):
        job_id = 'get_part-' + report_type + '-' + basename_from_key(report_args)
        r = self.context.get_report(report_type, **report_args)
        job_id += '-' + url.replace('/', '_')  # XXX
        part = self.context.comp(get_node, url=url, r=r, strict=strict, job_id=job_id)
        return part
    
    @contract(returns=Promise)
    def get_job(self):
        return self.context.comp(execute_proxy, self.operations) 
    

@contract(url=str, r=Report, returns=Report)
def get_node(url, r, strict=True):
    try:
        node = r.resolve_url(url)
    except NotExistent as e:
        if strict:
            logger.error('Error while getting url %r\n%s' % (url,
                                                             r.format_tree()))
            raise
        else:
            logger.warn('Ignoring error: %s' % e)
            return Report()

    node = deepcopy(node)
    node.parent = None
    return node


@contract(resources='dict', id_parent='str', child=Report, nid='str')
def add_child_with_id(resources, id_parent, child, nid):
    parent = resources[id_parent]
    child.nid = nid
    print(child.format_tree())
    parent.add_child(child)

    
@contract(resources='dict', id_parent='str', nid='str')
def rp_create_figure(resources, id_parent, nid, **figargs):
    parent = resources[id_parent]
    resources[nid] = parent.figure(nid=nid, **figargs)


@contract(resources='dict', id_figure='str', what='str')
def rp_figure_sub(resources, id_figure, what, caption=None):
    figure = resources[id_figure]
    try:
        figure.sub(what, caption=caption)
    except (NotExistent, Exception) as e:
        logger.error(e)
        

def execute_proxy(operations):
    report = Report()
    resources = {}
    resources['report'] = report
    for what, kwargs in operations:
        what(resources=resources, **kwargs)
    print(report.format_tree())
    return report
