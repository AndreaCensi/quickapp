#!/usr/bin/env python
# from quickapp import QuickApp
# from reprep import Report
# import sys
#
# def actual_computation(param1, param2, iteration):
#     pass
#
# def report(param2, jobs):  # @UnusedVariable
#     r = Report()
#
#     return r
#
# class QuickAppDemo1(QuickApp):
#
#     def define_options(self, params):
#         params.add_int('param1', help='First parameter', default=1)
#         params.add_int_list('param2', help='Second parameter')
#
#     def define_jobs_context(self, context):
#         options = self.get_options()
#
#         jobs = self.comp_comb(actual_computation,
#                               param1=options.param1,
#                               param2=options.param2,
#                               iteration=QuickApp.choice(range(4)))
#
#         rm = self.get_report_manager()
#         for param2, samples in jobs.groups_by_field_value('param2'):
#             rj = self.comp(report, param2, samples)
#             rm.add(rj, 'report', param2=param2)
#
#
#
# def compapp_test1():
#     args = ['-o', 'quickapp_test1',
#             '-c', 'make all', '--param1', '10', '--param2', '1,2,3']
#     QuickAppDemo1().main(args)
#
#
# if __name__ == '__main__':
#     sys.exit(QuickAppDemo1().main())
#
