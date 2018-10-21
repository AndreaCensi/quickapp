#!/usr/bin/env python
from compmake.jobs import all_jobs
from nose.tools import istest
from quickapp import (CompmakeContext, QuickApp, quickapp_main,
                      iterate_context_names)

from .quickappbase import QuickappTest


def f(name):
    print(name)
    return name


def define_jobs(context, id_name):
    assert isinstance(context, CompmakeContext)
    context.comp(f, id_name)


class QuickAppDemoChild(QuickApp):

    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        names = ['a', 'b', 'c']
        for c, id_name in iterate_context_names(context, names):
            define_jobs(c, id_name)


# XXX
# @istest
class CompappTestDynamic(QuickappTest):

    def compapp_test1(self):
        args = '--contracts -o %s -c make --compress' % self.root0
        ret_found = quickapp_main(QuickAppDemoChild, args.split(), sys_exit=False)
        self.assertEqual(0, ret_found)
        print('jobs in %s: %s' % (self.db, list(all_jobs(self.db))))
        self.assertJobsEqual('all', ['a-f', 'b-f', 'c-f'])


class QuickAppDemoChild2(QuickApp):

    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        names = ['a', 'b', 'c']
        for c, id_name in iterate_context_names(context, names):
            c.comp_dynamic(define_jobs, id_name)


@istest
class CompappTestDynamic2(QuickappTest):

    def compapp_test1(self):
        self.run_quickapp(qapp=QuickAppDemoChild2, cmd='ls')

        # These are the jobs currently defined
        self.assertJobsEqual('all', ['a-define_jobs',
                                     'b-define_jobs',
                                     'c-define_jobs',
                                     'a-context',
                                     'b-context',
                                     'c-context'])

        self.assert_cmd_success_script('make *-define_jobs; ls')

        self.assertJobsEqual('all', ['a-define_jobs',
                                     'b-define_jobs',
                                     'c-define_jobs',
                                     'a-context',
                                     'b-context',
                                     'c-context',
                                     'a-f', 'b-f', 'c-f'])

        self.assertJobsEqual('done', ['a-define_jobs',
                                      'b-define_jobs',
                                      'c-define_jobs',
                                      'a-context',
                                      'b-context',
                                      'c-context'])

        self.assert_cmd_success_script('make; ls')

        self.assertJobsEqual('done', ['a-define_jobs',
                                      'b-define_jobs',
                                      'c-define_jobs',
                                      'a-context',
                                      'b-context',
                                      'c-context',
                                      'a-f', 'b-f', 'c-f'])
