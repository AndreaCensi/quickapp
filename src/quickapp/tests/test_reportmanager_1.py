from nose.tools import istest

from quickapp import QuickApp, iterate_context_names
from reprep import Report

from .quickappbase import QuickappTest


def report_example1(param1, param2):
    r = Report()
    r.text('type', 'This is one report')
    r.text('param1', '%s' % param1)
    r.text('param2', '%s' % param2)
    return r

def report_example2(param1, param2):
    r = Report()
    r.text('type', 'This is another report')
    r.text('param1', '%s' % param1)
    r.text('param2', '%s' % param2)
    return r

class QuickAppDemoReport(QuickApp):

    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        param1s = ['a', 'b']
        param2s = [1, 2]
        
        for c1, param1 in iterate_context_names(context, param1s):
            c1.add_extra_report_keys(param1=param1)
            for c2, param2 in iterate_context_names(c1, param2s):
                c2.add_extra_report_keys(param2=param2)
                r = c2.comp(report_example1, param1=param1, param2=param2)
                c2.add_report(r, 'report_example1')
                r = c2.comp(report_example2, param1=param1, param2=param2)
                c2.add_report(r, 'report_example2')
        


@istest
class CompappTest1(QuickappTest):

    def compapp_test1(self):
        self.run_quickapp(QuickAppDemoReport, cmd='ls')
        print('---- now make')
        self.assert_cmd_success('make')
        print('---- result of first make')
        self.assert_cmd_success('ls')
        print('---- result of remake')
        self.assert_cmd_success('ls')
        self.assert_cmd_success('make')
        self.assert_cmd_success('ls')
#         self.assert_cmd_success('make')

