import inspect
import os
from typing import Any, Callable, Concatenate, List, Mapping, Optional, ParamSpec, TypeVar

from compmake import CMJobID, Context, load_static_storage, Promise
from conf_tools import ConfigState, GlobalConfig
from zuper_commons.fs import DirPath, joind, joinf
from zuper_commons.types import check_isinstance, ZTypeError, ZValueError
from .report_manager import ReportManager
from .resource_manager import ResourceManager

__all__ = [
    "QuickAppContext",
    "context_get_merge_data",
]

P = ParamSpec("P")
X = TypeVar("X")


class QuickAppContext:
    parent: "Optional[QuickAppContext]"
    _resource_manager: ResourceManager
    _report_manager: ReportManager
    private_report_manager: bool
    _output_dir: DirPath
    _extra_dep: list[Promise]
    _promise: Optional[Promise]
    _jobs: dict[CMJobID, Promise] = {}
    branched_children: "list[QuickAppContext]"
    branched_contexts: "list[Promise]"
    _job_prefix: str
    ngenerations: int

    def __init__(
        self,
        cc: Context,
        parent: "Optional[QuickAppContext]",
        job_prefix: Optional[str],
        output_dir: DirPath,
        extra_dep: Optional[list[CMJobID]] = None,
        resource_manager: Optional[ResourceManager] = None,
        extra_report_keys=None,
        report_manager=None,
    ):
        self.ngenerations = 0
        check_isinstance(cc, Context)
        check_isinstance(parent, (QuickAppContext, type(None)))
        if extra_dep is None:
            extra_dep = []
        self.cc = cc
        self._promise = None
        # can be removed once subtask() is removed
        # self._qapp = qapp
        # only used for count invocation
        self._parent = parent
        self._job_prefix = job_prefix

        if resource_manager is None:
            resource_manager = ResourceManager(self)

        if report_manager is None:
            self.private_report_manager = True  # only create indexe if this is true
            reports = joind(output_dir, "report")
            reports_index = joinf(output_dir, "report.html")
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

        self.branched_contexts = []
        self.branched_children = []
        self.children_names = set()

    n_comp_invocations: int

    def __str__(self) -> str:
        return f"QuickAppContext({self._job_prefix})"

    # def all_jobs(self):
    #     return list(self._jobs.values())

    def all_jobs_dict(self):
        return dict(self._jobs)

    def checkpoint(self, job_name: str) -> Promise:
        """

        (DEPRECATED)

        Creates a dummy job called "job_name" that depends on all jobs
        previously defined; further, this new job is put into _extra_dep.
        This means that all successive jobs will require that the previous
        ones be done.

        Returns the checkpoint job (CompmakePromise).
        """
        # noinspection PyTypeChecker
        job_checkpoint: Promise = self.comp(
            checkpoint, job_name, prev_jobs=list(self._jobs.values()), job_id=job_name
        )  # type: ignore
        self._extra_dep.append(job_checkpoint)
        assert isinstance(job_checkpoint, Promise)
        return job_checkpoint

    #
    # Wrappers form Compmake's "comp".
    #
    def comp(self, f: Callable[P, X], *args: P.args, job_id: Optional[str] = None, **kwargs: P.kwargs) -> X:
        # Promise:
        """
        Simple wrapper for Compmake's comp function.
        Use this instead of "comp".
        """
        self.count_comp_invocations()
        self.cc.comp_prefix(self._job_prefix)

        other_extra = kwargs.get("extra_dep", [])
        if isinstance(other_extra, Promise):
            other_extra = [other_extra]

        extra_dep = self._extra_dep + other_extra
        kwargs["extra_dep"] = extra_dep
        promise = self.cc.comp(f, *args, job_id=job_id, **kwargs)
        self._jobs[promise.job_id] = promise
        return promise

    def comp_dynamic(
        self,
        f: "Callable[Concatenate[QuickAppContext, P], X]",
        *args: P.args,
        job_id: Optional[str] = None,
        **kwargs: P.kwargs,
    ) -> X:
        # jb = job_id if job_id else f.__name__
        # jn = f'{jb}-context-{id(self)}'
        # context = self.comp(load_static_storage, self, job_id=jn)
        # assert context is not None
        context = self._get_promise()

        compmake_args = {"job_id": job_id}
        compmake_args_name = ["job_id", "extra_dep", "command_name"]
        for n in compmake_args_name:
            if n in kwargs:
                compmake_args[n] = kwargs[n]
                del kwargs[n]

        if not "command_name" in compmake_args:
            compmake_args["command_name"] = f.__name__
        #:arg:job_id:   sets the job id (respects job_prefix)
        #:arg:extra_dep: extra dependencies (not passed as arguments)
        #:arg:command_name: used to define job name if job_id not provided.

        is_async = inspect.iscoroutinefunction(f)
        if is_async:
            both = self.cc.comp_dynamic(
                _dynreports_wrap_dynamic_async,
                qc=context,
                function=f,
                args=args,
                kw=kwargs,
                **compmake_args,
            )
        else:
            both = self.cc.comp_dynamic(
                _dynreports_wrap_dynamic,
                qc=context,
                function=f,
                args=args,
                kw=kwargs,
                **compmake_args,
            )
        result = self.comp(_dynreports_getres, both)
        data = self.comp(_dynreports_getbra, both)
        self.branched_contexts.append(data)  # type: ignore
        return result

    def comp_config(self, f, *args, **kwargs) -> Promise:
        """
        Like comp, but we also automatically save the GlobalConfig state.
        """
        config_state = GlobalConfig.get_state()
        # so that compmake can use a good name
        if not "command_name" in kwargs:
            kwargs["command_name"] = f.__name__
        return self.comp(wrap_state, config_state, f, *args, **kwargs)

    def comp_config_dynamic(self, f, *args, **kwargs) -> Promise:
        """Defines jobs that will take a "context" argument to define
        more jobs."""
        config_state = GlobalConfig.get_state()
        # so that compmake can use a good name
        if not "command_name" in kwargs:
            kwargs["command_name"] = f.__name__
        return self.comp_dynamic(wrap_state_dynamic, config_state, f, *args, **kwargs)

    def count_comp_invocations(self) -> None:
        self.n_comp_invocations += 1
        if self._parent is not None:
            self._parent.count_comp_invocations()

    def get_output_dir(self):
        """Returns a suitable output directory for data files"""
        # only create output dir on demand
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir, exist_ok=True)

        return self._output_dir

    def child(
        self,
        name: str,
        add_job_prefix: Optional[str] = None,
        add_outdir: Optional[DirPath] = None,
        extra_dep: list[Any] = None,
        extra_report_keys: Optional[Mapping[str, Any]] = None,
        separate_resource_manager: bool = False,
        separate_report_manager: bool = False,
    ) -> "QuickAppContext":
        if extra_dep is None:
            extra_dep = []
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
        # if qapp is None:
        #     qapp = self._qapp

        name_friendly = name.replace("-", "_").replace(".", "_")
        if name_friendly in self.children_names:
            msg = f'Child with name "{name_friendly}" already exists.'
            raise ZValueError(msg, job_prefix=self._job_prefix, children_names=self.children_names)
        self.children_names.add(name_friendly)

        if add_job_prefix is None:
            add_job_prefix = name_friendly

        if add_outdir is None:
            add_outdir = name_friendly

        if add_job_prefix:
            if self._job_prefix is None:
                job_prefix = add_job_prefix
            else:
                job_prefix = self._job_prefix + "-" + add_job_prefix
        else:
            job_prefix = self._job_prefix

        if add_outdir:
            output_dir = joind(self._output_dir, add_outdir)
        else:
            output_dir = self._output_dir

        if separate_report_manager:
            if not add_outdir:
                msg = (
                    "Asked for separate report manager, but without changing output dir. "
                    "This will make the report overwrite each other."
                )
                raise ZValueError(msg, name=name)

            report_manager = None
        else:
            report_manager = self._report_manager

        if separate_resource_manager:
            resource_manager = None  # QuickAppContext will create its own
        else:
            resource_manager = self._resource_manager

        _extra_dep = self._extra_dep + extra_dep

        extra_report_keys_ = {}
        extra_report_keys_.update(self.extra_report_keys)
        if extra_report_keys is not None:
            extra_report_keys_.update(extra_report_keys)

        c1 = QuickAppContext(
            cc=self.cc,
            parent=self,
            job_prefix=job_prefix,
            output_dir=output_dir,
            report_manager=report_manager,
            resource_manager=resource_manager,
            extra_report_keys=extra_report_keys_,
            extra_dep=_extra_dep,
        )
        self.branched_children.append(c1)

        return c1

    def add_job_defined_in_this_session(self, job_id: CMJobID):
        self.cc.add_job_defined_in_this_session(job_id)
        if self._parent is not None:
            self._parent.add_job_defined_in_this_session(job_id)

    # async def subtask(
    #     self,
    #     sti: SyncTaskInterface,
    #     task,
    #     extra_dep: Optional[List[str]] = None,
    #     add_job_prefix=None,
    #     add_outdir=None,
    #     separate_resource_manager=False,
    #     separate_report_manager=False,
    #     extra_report_keys=None,
    #     **task_config,
    # ):
    #     extra_dep = extra_dep or []
    #     return await self._qapp.call_recursive(
    #         sti,
    #         context=self,
    #         child_name=task.cmd,
    #         cmd_class=task,
    #         args=task_config,
    #         extra_dep=extra_dep,
    #         add_outdir=add_outdir,
    #         add_job_prefix=add_job_prefix,
    #         extra_report_keys=extra_report_keys,
    #         separate_report_manager=separate_report_manager,
    #         separate_resource_manager=separate_resource_manager,
    #     )

    # Resource managers
    def get_resource_manager(self) -> ResourceManager:
        return self._resource_manager

    def needs(self, rtype, **params):
        rm = self.get_resource_manager()
        res = rm.get_resource_job(self, rtype, **params)
        check_isinstance(res, Promise)
        self._extra_dep.append(res)

    def get_resource(self, rtype: str, **params: Any) -> Promise:
        rm = self.get_resource_manager()
        return rm.get_resource_job(self, rtype, **params)

    def add_report(self, report: Any, report_type: str, **params: Any) -> None:
        rm = self.get_report_manager()
        params.update(self.extra_report_keys)
        rm.add(self, report, report_type, **params)

    def get_report(self, report_type: str, **params) -> Promise:
        """Returns the promise to the given report"""
        rm = self.get_report_manager()
        return rm.get(report_type, **params)

    def get_report_manager(self) -> ReportManager:
        return self._report_manager

    def add_extra_report_keys(self, **keys):
        for k in keys:
            if k in self.extra_report_keys:
                msg = "key %r already in %s" % (k, list(self.extra_report_keys))
                raise ValueError(msg)
        self.extra_report_keys.update(keys)

    def _get_promise(self) -> Promise:
        """Returns the promise object representing this context."""
        if self._promise is None:
            # warnings.warn('Need IDs for contexts, using job_prefix.')
            # warnings.warn('XXX: Note that this sometimes creates a context '
            #              'with depth 1; then "delete not root" deletes it.')
            self._promise_job_id = "context"
            self._promise = self.comp(load_static_storage, self, job_id=self._promise_job_id)
        return self._promise

    def has_branched(self) -> bool:
        """Returns True if any comp_dynamic was issued."""
        return len(self.branched_contexts) > 0 or any([c.has_branched() for c in self.branched_children])

    def __getstate__(self) -> Any:
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # logger.info('getstate', state=state)
        # if state['_promise'] is None:
        #     raise ZValueError('pickling before promise is created')
        if "cc" in state:
            state.pop("cc")

        state["ngenerations"] += 1
        # # Remove the unpicklable entries.
        # for k, v in state.items():
        #     try:
        #         pickle.dumps(v)
        #     except BaseException as e:
        #         msg = f'Cannot pickle member {k!r}'
        #         raise ZValueError(msg, k=k, v=v) from e

        return state


def wrap_state(config_state: ConfigState, f, *args, **kwargs):
    """Used internally by comp_config()"""
    config_state.restore()
    return f(*args, **kwargs)


def wrap_state_dynamic(context: QuickAppContext, config_state: ConfigState, f, *args, **kwargs):
    """Used internally by comp_config_dynamic()"""
    config_state.restore()
    return f(context, *args, **kwargs)


# noinspection PyUnusedLocal
def checkpoint(name, prev_jobs):
    pass


async def _dynreports_wrap_dynamic_async(context: Context, qc: QuickAppContext, function, args, kw) -> dict:
    """"""
    assert qc is not None, (function,)
    # assert qc._promise is not None, qc.__dict__
    qc.cc = context

    res = {}
    try:
        res["f-result"] = await function(qc, *args, **kw)
    except TypeError as e:
        msg = "Could not call %r" % function
        raise ZTypeError(msg, args=args, kw=kw) from e

    res["context-res"] = context_get_merge_data(qc)
    return res


def _dynreports_wrap_dynamic(context: Context, qc: QuickAppContext, function, args, kw) -> dict:
    """"""
    assert qc is not None, (function,)
    # assert qc._promise is not None, qc.__dict__
    qc.cc = context

    res = {}
    try:
        res["f-result"] = function(qc, *args, **kw)
    except TypeError as e:
        msg = "Could not call %r" % function
        raise ZTypeError(msg, args=args, kw=kw) from e

    res["context-res"] = context_get_merge_data(qc)
    return res


def _dynreports_merge(branched: List[dict]):
    rm = None
    for i, b in enumerate(branched):
        if i == 0:
            rm = b["report_manager"]
        else:
            rm.merge(b["report_manager"])
    return dict(report_manager=rm)


def _dynreports_getres(res: dict):
    """gets only the result"""
    return res["f-result"]


def _dynreports_getbra(res) -> dict:
    """gets only the result"""
    return res["context-res"]


def get_branched_contexts(context):
    """Returns all promises created by context_comp_dynamic() for this and children."""
    res = list(context.branched_contexts)
    for c in context.branched_children:
        res.extend(get_branched_contexts(c))
    return res


def context_get_merge_data(context: QuickAppContext) -> Any:
    rm = context.get_report_manager()
    data = [dict(report_manager=rm)]

    data.extend(get_branched_contexts(context))

    if len(data) > 1:
        return context.cc.comp(_dynreports_merge, data)
    else:
        return data[0]
