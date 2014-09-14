from nose.tools import istest

from quickapp import QuickApp, iterate_context_names

from .quickappbase import QuickappTest


def f(name):
    print(name)
    return name

def define_jobs2(context, id_name):
    context.comp(f, id_name)

def define_jobs1(context, id_name):
    names2 = ['m', 'n']
    for c2, name2 in iterate_context_names(context, names2):
        #assert c2.currently_executing == context.currently_executing
        c2.comp_dynamic(define_jobs2, id_name + name2)


class QuickAppDemoChild4(QuickApp):

    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        names1 = ['a', 'b']
        for c1, name1 in iterate_context_names(context, names1):
            c1.comp_dynamic(define_jobs1, name1)

@istest
class TestDynamic4(QuickappTest):

    howmany = None  # used by cases()

    def test_dynamic4(self):
        self.run_quickapp(qapp=QuickAppDemoChild4, cmd='ls')
        self.assertJobsEqual('all', ['a-context',
                                     'b-context',
                                     'a-define_jobs1',
                                     'b-define_jobs1', ])
        self.assert_cmd_success('make *define_jobs1;ls')
        self.assertJobsEqual('all', ['a-context',
                                     'b-context',
                                     'a-define_jobs1',
                                     'b-define_jobs1',
                                     'a-m-context',
                                     'a-n-context',
                                     'b-m-context',
                                     'b-n-context',
                                     'a-m-define_jobs2',
                                     'b-m-define_jobs2',
                                     'a-n-define_jobs2',
                                     'b-n-define_jobs2', ])


        self.assert_cmd_success('details a-define_jobs1')
        self.assert_defined_by('a-define_jobs1', ['root'])

        self.assert_cmd_success('make;ls')
        self.assertJobsEqual('all', ['a-context',
                                     'b-context',
                                     'a-define_jobs1',
                                     'b-define_jobs1',
                                     'a-m-context',
                                     'a-n-context',
                                     'b-m-context',
                                     'b-n-context',
                                     'a-m-define_jobs2',
                                     'b-m-define_jobs2',
                                     'a-n-define_jobs2',
                                     'b-n-define_jobs2',
                                     'a-m-f',
                                     'a-n-f',
                                     'b-m-f',
                                     'b-n-f',
                                     ])

        self.assert_cmd_success('details a-m-define_jobs2')
        self.assert_defined_by('a-m-define_jobs2', ['root', 'a-define_jobs1'])


        self.assert_cmd_success('details a-m-f')
        self.assert_defined_by('a-m-f', ['root', 'a-define_jobs1', 'a-m-define_jobs2'])
