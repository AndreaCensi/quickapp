#!/usr/bin/env python
from shutil import rmtree
from tempfile import mkdtemp
import os
from nose.tools import istest
from quickapp import (QuickApp, QUICKAPP_USER_ERROR, QUICKAPP_COMPUTATION_ERROR,
                      quickapp_main)
from reprep import Report

from .quickappbase import QuickappTest


def actual_computation(param1, param2):
    print('computing (%s %s)' % (param1, param2))
    return [1, 2, 3, 4]


def report_example(param2, samples):
    print('report_example(%s, %s)' % (param2, samples))
    if param2 == -1:
        print('generating exception')
        raise Exception('fake exception')
    r = Report()
    r.text('samples', str(samples))
    print('creating report')
    return r


class QuickAppDemo2(QuickApp):
    cmd = 'quick-app-demo'

    def define_options(self, params):
        params.add_int('param1', help='First parameter', default=1)
        params.add_int('param2', help='Second parameter')

    def define_jobs_context(self, context):
        options = self.get_options()
        param1 = options.param1
        param2 = options.param2
        samples = context.comp(actual_computation, param1=param1, param2=param2)

        rj = context.comp(report_example, param2, samples)
        context.add_report(rj, 'report_example')


@istest
class CompappTest1(QuickappTest):

    def compapp_test1(self):
        cases = []

        def add(args, ret):
            cases.append(dict(args=args, ret=ret))

        add('--compress --contracts -c clean;make --param1 10 --param2 1', 0)

        # parse error
        add('--compress --contracts -c clean;make  --param1 10 --parm2 1 ',
            QUICKAPP_USER_ERROR)

        # computation exception
        add('--compress --contracts  -c clean;make  --param1 10 --param2 -1 ',
            QUICKAPP_COMPUTATION_ERROR)

        for c in cases:
            args = c['args']

            if isinstance(args, str):
                args = args.split()
            tmpdir = mkdtemp()
            args = ['-o', tmpdir] + args
            ret = c['ret']
            with open(os.path.join(tmpdir, '.compmake.rc'), 'w') as f:
                f.write('config echo 1\n')
            ret_found = quickapp_main(QuickAppDemo2, args, sys_exit=False)
            msg = 'Expected %d, got %d.\nArguments: %s ' % (ret, ret_found, c['args'])
            self.assertEqual(ret, ret_found, msg)
            rmtree(tmpdir)


if __name__ == '__main__':
    quickapp_main(QuickAppDemo2)
