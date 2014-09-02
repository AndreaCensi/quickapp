from quickapp import QuickApp, iterate_context_names
from reprep import Report
 
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

def instance_reports(context):
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


class QuickAppDemoReport(QuickApp):

    def define_options(self, params):
        pass

    def define_jobs_context(self, context):
        context.comp_dynamic(instance_reports)
        
        #context.create_dynamic_index_job()

if __name__ == '__main__':
    main = QuickAppDemoReport.get_sys_main()
    main()
