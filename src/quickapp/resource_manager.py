from collections import defaultdict
import traceback

from contracts import contract, describe_type

from compmake import Promise
from conf_tools.utils import check_is_in, indent
from reprep.report_utils import StoreResults


__all__ = ['ResourceManager']


class ResourceManager(object):
    class CannotProvide(Exception):
        pass

    def __init__(self, context):
        from quickapp.compmake_context import CompmakeContext
        assert isinstance(context, CompmakeContext), context
        self.allresources = StoreResults()
        self.providers = defaultdict(list)  # rtype => list of providers
        self.make_prefix = {}  # rtype => function to make prefix
        self._context = context

    @contract(rtype='str')
    def set_resource_provider(self, rtype, provider):
        """
            provider: any callable. It will be called with "context" as first 
                argument, and with any remaining params. It needs to return
                a Compmake Promise() object (i.e. the output of comp()). 
                
        """
        self.providers[rtype].append(provider)

    def set_resource_prefix_function(self, rtype, make_prefix):
        """
            make_prefix: a function that takes (rtype, **params) and 
            returns a string.
        """
        self.make_prefix[rtype] = make_prefix

    @contract(rtype='str')
    def get_resource(self, rtype, **params):
        return self.get_resource_job(self._context, rtype, **params)

    @contract(rtype='str')
    def get_resource_job(self, context, rtype, **params):
        # print('RM %s %s get_resource %s %s' % (id(self), self._context, rtype, params))
        key = dict(rtype=rtype, **params)
        already_done = key in self.allresources
        if already_done:
            return self.allresources[key]

        check_is_in('resource type', rtype, self.providers)

        prefix = self._make_prefix(rtype, **params)
        #         print('adding job prefix %r' % prefix)
        c = context.child(name=rtype, add_job_prefix=prefix, add_outdir=rtype)
        c._job_prefix = prefix
        # Add this point we should check if we already created the job
        ok = []
        errors = []
        for provider in self.providers[rtype]:
            try:
                res_i = provider(c, **params)
                ok.append((provider, res_i))
            except ResourceManager.CannotProvide as e:
                errors.append(e)
            except Exception as e:
                msg = 'Error while trying to get resource.\n'
                msg += ' type: %r params: %s\n' % (rtype, params)
                msg += 'While calling provider %r:\n' % provider
                msg += indent(traceback.format_exc(), '> ')
                raise Exception(msg)

        if not ok:
            msg = 'No provider could create this resource:\n'
            msg += "\n".join('- %s' % str(e) for e in errors)
            raise Exception(msg)

        if len(ok) >= 2:
            msg = 'The same resource could be created by two providers.'
            msg += '\n%s %s' % (rtype, params)
            for prov, _ in ok:
                msg += '\n - %s' % prov
            raise Exception(msg)

        assert len(ok) == 1
        res = ok[0][1]
        self.set_resource(res, rtype, **params)
        return res

    def _make_prefix(self, rtype, **params):
        """ Creates the job prefix for the given resource. """
        # use the user-defined if available
        if rtype in self.make_prefix:
            f = self.make_prefix[rtype]
            return f(rtype, **params)

        keys = sorted(list(params.keys()))

        from quickapp.app_utils.minimal_name import good_context_name
        vals = [good_context_name(str(params[k])) for k in keys]
        rtype = rtype.replace('-', '_')
        alls = [rtype] + vals
        prefix = "-".join(alls)
        return prefix

    @contract(rtype='str')
    def set_resource(self, goal, rtype, **params):
        key = dict(rtype=rtype, **params)
        if not isinstance(goal, Promise):
            msg = 'Warning, resource did not return a Compmake Promise.'
            msg += '\n  key: %s' % key
            msg += '\n type: %s' % describe_type(goal)
            # logger.error(msg)
            raise ValueError(msg)

        self.allresources[key] = goal
         
