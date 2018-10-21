
import os

from compmake import Context, Promise
from compmake.context import load_static_storage
from conf_tools import GlobalConfig
from contracts import check_isinstance
from contracts import contract, describe_type
from contracts.utils import raise_wrapped

from .report_manager import ReportManager
from .resource_manager import ResourceManager

__all__ = [
    'CompmakeContext',
    'QuickAppContext',
]


class QuickAppContext(object):

    @contract(extra_dep='list', cc=Context)
    def __init__(self, cc, qapp, parent, job_prefix,
                 output_dir, extra_dep=[], resource_manager=None,
                 extra_report_keys=None,
                 report_manager=None):
        check_isinstance(cc, Context)
        check_isinstance(parent, (CompmakeContext, type(None)))
        self.cc = cc
        # can be removed once subtask() is removed
        self._qapp = qapp
        # only used for count invocation
        self._parent = parent
        self._job_prefix = job_prefix

        if resource_manager is None:
            resource_manager = ResourceManager(self)

        if report_manager is None:
            self.private_report_manager = True  # only create indexe if this is true
            reports = os.path.join(output_dir, 'report')
            reports_index = os.path.join(output_dir, 'report.html')
            report_manager = ReportManager(self, reports, reports_index)
        else:
            self.private_report_manager = False

        self._report_manager = report_manager
        self._resource_manager = resource_manager
        self._output_dir = output_dir
        self.n_comp_invocations = 0
        self._extra_dep = extra_dep
        self._jobs = {}
        if extra_report_keys is None:
            extra_report_keys = {}
        self.extra_report_keys = extra_report_keys

        self._promise = None

        self.branched_contexts = []
        self.branched_children = []

    def __str__(self):
        return 'CompmakeContext(%s)' % (self._job_prefix)

    # def all_jobs(self):
    #     return list(self._jobs.values())

    def all_jobs_dict(self):
        return dict(self._jobs)

    @contract(job_name='str', returns=Promise)
    def checkpoint(self, job_name):
        """

            (DEPRECATED)

            Creates a dummy job called "job_name" that depends on all jobs
            previously defined; further, this new job is put into _extra_dep.
            This means that all successive jobs will require that the previous
            ones be done.

            Returns the checkpoint job (CompmakePromise).
        """
        job_checkpoint = self.comp(checkpoint, job_name,
                                   prev_jobs=list(self._jobs.values()),
                                   job_id=job_name)
        self._extra_dep.append(job_checkpoint)
        return job_checkpoint

    #
    # Wrappers form Compmake's "comp".
    #
    @contract(returns=Promise)
    def comp(self, f, *args, **kwargs):
        """
            Simple wrapper for Compmake's comp function.
            Use this instead of "comp".
        """
        self.count_comp_invocations()
        self.cc.comp_prefix(self._job_prefix)

        other_extra = kwargs.get('extra_dep', [])
        if isinstance(other_extra, Promise):
            other_extra = [other_extra]

        extra_dep = self._extra_dep + other_extra
        kwargs['extra_dep'] = extra_dep
        promise = self.cc.comp(f, *args, **kwargs)
        self._jobs[promise.job_id] = promise
        return promise

    @contract(returns=Promise)
    def comp_dynamic(self, f, *args, **kwargs):
        # XXX: we really dont need it
        context = self._get_promise()
        # context = self

        compmake_args = {}
        compmake_args_name = ['job_id', 'extra_dep', 'command_name']
        for n in compmake_args_name:
            if n in kwargs:
                compmake_args[n] = kwargs[n]
                del kwargs[n]

        if not 'command_name' in compmake_args:
            compmake_args['command_name'] = f.__name__
        #:arg:job_id:   sets the job id (respects job_prefix)
        #:arg:extra_dep: extra dependencies (not passed as arguments)
        #:arg:command_name: used to define job name if job_id not provided.

        both = self.cc.comp_dynamic(_dynreports_wrap_dynamic, qc=context,
                             function=f, args=args, kw=kwargs,
                             **compmake_args)

        result = self.comp(_dynreports_getres, both)
        data = self.comp(_dynreports_getbra, both)
        self.branched_contexts.append(data)
        return result

    @contract(returns=Promise)
    def comp_config(self, f, *args, **kwargs):
        """
            Like comp, but we also automatically save the GlobalConfig state.
        """
        config_state = GlobalConfig.get_state()
        # so that compmake can use a good name
        if not 'command_name' in kwargs:
            kwargs['command_name'] = f.__name__
        return self.comp(wrap_state, config_state, f, *args, **kwargs)

    @contract(returns=Promise)
    def comp_config_dynamic(self, f, *args, **kwargs):
        """ Defines jobs that will take a "context" argument to define
            more jobs. """
        config_state = GlobalConfig.get_state()
        # so that compmake can use a good name
        if not 'command_name' in kwargs:
            kwargs['command_name'] = f.__name__
        return self.comp_dynamic(wrap_state_dynamic, config_state, f, *args, **kwargs)

    def count_comp_invocations(self):
        self.n_comp_invocations += 1
        if self._parent is not None:
            self._parent.count_comp_invocations()

    def get_output_dir(self):
        """ Returns a suitable output directory for data files """
        # only create output dir on demand
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

        return self._output_dir

    @contract(extra_dep='list', name=str)
    def child(self, name, qapp=None,
              add_job_prefix=None,
              add_outdir=None,
              extra_dep=[],
              extra_report_keys=None,
              separate_resource_manager=False,
              separate_report_manager=False):
        """
            Returns child context

            add_job_prefix =
                None (default) => use "name"
                 '' => do not add to the prefix

            add_outdir:
                None (default) => use "name"
                 '' => do not add outdir

            separate_resource_manager: If True, create a child of the ResourceManager,
            otherwise we just use the current one and its context.
        """
        check_isinstance(name, str)
        if qapp is None:
            qapp = self._qapp

        name_friendly = name.replace('-', '_')

        if add_job_prefix is None:
            add_job_prefix = name_friendly

        if add_outdir is None:
            add_outdir = name_friendly

        if add_job_prefix != '':
            if self._job_prefix is None:
                job_prefix = add_job_prefix
            else:
                job_prefix = self._job_prefix + '-' + add_job_prefix
        else:
            job_prefix = self._job_prefix

        if add_outdir != '':
            output_dir = os.path.join(self._output_dir, name)
        else:
            output_dir = self._output_dir

        if separate_report_manager:
            if add_outdir == '':
                msg = ('Asked for separate report manager, but without changing output dir. '
                       'This will make the report overwrite each other.')
                raise ValueError(msg)

            report_manager = None
        else:
            report_manager = self._report_manager

        if separate_resource_manager:
            resource_manager = None  # CompmakeContext will create its own
        else:
            resource_manager = self._resource_manager

        _extra_dep = self._extra_dep + extra_dep

        extra_report_keys_ = {}
        extra_report_keys_.update(self.extra_report_keys)
        if extra_report_keys is not None:
            extra_report_keys_.update(extra_report_keys)

        c1 = CompmakeContext(cc=self.cc,
                            qapp=qapp, parent=self,
                            job_prefix=job_prefix,
                            report_manager=report_manager,
                            resource_manager=resource_manager,
                            extra_report_keys=extra_report_keys_,
                            output_dir=output_dir,
                            extra_dep=_extra_dep)
        self.branched_children.append(c1)
        return c1

    @contract(job_id=str)
    def add_job_defined_in_this_session(self, job_id):
        self.cc.add_job_defined_in_this_session(self, job_id)
        if self._parent is not None:
            self._parent.add_job_defined_in_this_session(job_id)

    @contract(extra_dep='list')
    def subtask(self, task, extra_dep=[], add_job_prefix=None, add_outdir=None,
                    separate_resource_manager=False,
                    separate_report_manager=False,
                    extra_report_keys=None,
                    **task_config):
        return self._qapp.call_recursive(context=self, child_name=task.cmd,
                                         cmd_class=task, args=task_config,
                                         extra_dep=extra_dep,
                                         add_outdir=add_outdir,
                                         add_job_prefix=add_job_prefix,
                                         extra_report_keys=extra_report_keys,
                                         separate_report_manager=separate_report_manager,
                                         separate_resource_manager=separate_resource_manager)

    # Resource managers
    @contract(returns=ResourceManager)
    def get_resource_manager(self):
        return self._resource_manager

    def needs(self, rtype, **params):
        rm = self.get_resource_manager()
        res = rm.get_resource_job(self, rtype, **params)
        assert isinstance(res, Promise), describe_type(res)
        self._extra_dep.append(res)

    def get_resource(self, rtype, **params):
        rm = self.get_resource_manager()
        return rm.get_resource_job(self, rtype, **params)

    @contract(report=Promise, report_type='str')
    def add_report(self, report, report_type, **params):
        rm = self.get_report_manager()
        params.update(self.extra_report_keys)
        rm.add(self, report, report_type, **params)

    @contract(returns=Promise, report_type='str')
    def get_report(self, report_type, **params):
        """ Returns the promise to the given report """
        rm = self.get_report_manager()
        return rm.get(report_type, **params)

    def get_report_manager(self):
        return self._report_manager

    def add_extra_report_keys(self, **keys):
        for k in keys:
            if k in self.extra_report_keys:
                msg = 'key %r already in %s' % (k, list(self.extra_report_keys))
                raise ValueError(msg)
        self.extra_report_keys.update(keys)

    @contract(returns=Promise)
    def _get_promise(self):
        """ Returns the promise object representing this context. """
        if self._promise is None:
            #warnings.warn('Need IDs for contexts, using job_prefix.')
            #warnings.warn('XXX: Note that this sometimes creates a context '
            #              'with depth 1; then "delete not root" deletes it.')
            self._promise_job_id = 'context'
            self._promise = self.comp(load_static_storage, self,
                                      job_id=self._promise_job_id)
        return self._promise

    def has_branched(self):
        """ Returns True if any comp_dynamic was issued. """
        return (len(self.branched_contexts) > 0 or
                any([c.has_branched() for c in self.branched_children]))


def wrap_state(config_state, f, *args, **kwargs):
    """ Used internally by comp_config() """
    config_state.restore()
    return f(*args, **kwargs)


def wrap_state_dynamic(context, config_state, f, *args, **kwargs):
    """ Used internally by comp_config_dynamic() """
    config_state.restore()
    return f(context, *args, **kwargs)


def checkpoint(name, prev_jobs):
    pass


@contract(context=Context, returns='dict')
def _dynreports_wrap_dynamic(context, qc, function, args, kw):
    """

    """

    qc.cc = context

    res = {}
    try:
        res['f-result'] = function(qc, *args, **kw)
    except TypeError as e:
        msg = 'Could not call %r' % function
        raise_wrapped(TypeError, e, msg, args=args, kw=kw)

    res['context-res'] = context_get_merge_data(qc)
    return res


@contract(branched='list(dict)')
def _dynreports_merge(branched):
    rm = None
    for i, b in enumerate(branched):
        if i == 0:
            rm = b['report_manager']
        else:
            rm.merge(b['report_manager'])
    return dict(report_manager=rm)


@contract(res='dict')
def _dynreports_getres(res):
    """ gets only the result """
    return res['f-result']


@contract(res='dict')
def _dynreports_getbra(res):
    """ gets only the result """
    return res['context-res']


def get_branched_contexts(context):
    """ Returns all promises created by context_comp_dynamic() for this and children. """
    res = list(context.branched_contexts)
    for c in context.branched_children:
        res.extend(get_branched_contexts(c))
    return res


def context_get_merge_data(context):
    rm = context.get_report_manager()
    data = [dict(report_manager=rm)]

    data.extend(get_branched_contexts(context))

    if len(data) > 1:
        return context.cc.comp(_dynreports_merge, data)
    else:
        return data[0]


CompmakeContext = QuickAppContext

