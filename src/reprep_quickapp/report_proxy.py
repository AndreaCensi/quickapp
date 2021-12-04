import traceback
from copy import deepcopy

from compmake import Promise
from quickapp import QuickAppContext
from quickapp.report_manager import basename_from_key
from reprep import logger, NotExistent, Report

__all__ = ["ReportProxy", "get_node"]


class FigureProxy:
    def __init__(self, id_figure, report_proxy):
        self.id_figure = id_figure
        self.report_proxy = report_proxy

    def sub(self, what: str, **kwargs):
        self.report_proxy.op(rp_figure_sub, id_figure=self.id_figure, what=what, **kwargs)


class ReportProxy:
    def __init__(self, context: QuickAppContext):
        self.context = context
        self.operations = []
        self.resources = {}

    def op(self, function, **kwargs):
        self.operations.append((function, kwargs))

    def figure(self, nid: str, **kwargs):
        if nid is None:
            nid = "Figure"
        self.op(rp_create_figure, id_parent="report", nid=nid, **kwargs)
        return FigureProxy(nid, self)

    def add_child_with_id(self, child: Promise, nid: str):
        self.op(add_child_with_id, id_parent="report", child=child, nid=nid)

    def add_child_from_other(self, url, nid, report_type, strict=True, **report_args):
        part = self.get_part_of(url, report_type, strict=strict, **report_args)

        if nid is None:
            nid = basename_from_key(report_args) + "-" + url.replace("/", "-")  # XXX url chars

        self.add_child_with_id(part, nid)
        return nid

    def get_part_of(self, url: str, report_type: str, strict=True, **report_args) -> Promise:
        job_id = "get_part-" + report_type + "-" + basename_from_key(report_args)
        r = self.context.get_report(report_type, **report_args)
        job_id += "-" + url.replace("/", "_")  # XXX
        part = self.context.comp(get_node, url=url, r=r, strict=strict, job_id=job_id)
        return part

    def get_job(self) -> Promise:
        return self.context.comp(execute_proxy, self.operations)


def get_node(url: str, r: Report, strict=True) -> Report:
    try:
        node = r.resolve_url(url)
    except NotExistent as e:
        if strict:
            logger.error("Error while getting url %r\n%s" % (url, r.format_tree()))
            raise
        else:
            logger.warn("Ignoring error: %s" % e)
            return Report()

    node = deepcopy(node)
    node.parent = None
    return node


def add_child_with_id(resources: dict, id_parent: str, child: Report, nid: str):
    parent = resources[id_parent]
    child.nid = nid
    print(child.format_tree())
    parent.add_child(child)


def rp_create_figure(resources: dict, id_parent: str, nid: str, **figargs):
    parent = resources[id_parent]
    resources[nid] = parent.figure(nid=nid, **figargs)


def rp_figure_sub(resources: dict, id_figure: str, what: str, caption=None):
    figure = resources[id_figure]
    try:
        figure.sub(what, caption=caption)
    except (NotExistent, Exception) as e:
        logger.error(traceback.format_exc())


def execute_proxy(operations):
    report = Report()
    resources = {}
    resources["report"] = report
    for what, kwargs in operations:
        what(resources=resources, **kwargs)
    print(report.format_tree())
    return report
