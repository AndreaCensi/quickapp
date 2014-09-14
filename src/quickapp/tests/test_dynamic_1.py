from nose.tools import istest

from quickapp import QuickApp

from .quickappbase import QuickappTest


def f():
    return 1

def define_jobs2(context):
    context.comp(f)

def define_jobs1(context):
    context.comp_dynamic(define_jobs2)
    
class QuickAppDemoChild1(QuickApp):

    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        context.comp_dynamic(define_jobs1)

@istest
class TestDynamic1(QuickappTest):

    howmany = None  # used by cases()

    def test_dynamic1(self):
        self.run_quickapp(qapp=QuickAppDemoChild1, cmd='ls')
        self.assert_cmd_success('make define_jobs1')
        self.assert_cmd_success('ls')
        
        self.assert_cmd_success('make')
        self.assert_cmd_success('make')
        self.assert_cmd_success('make')
        
        

