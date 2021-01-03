#!/usr/bin/env python3

from quickapp import QuickApp


class AppExample(QuickApp):
    """ Simplest app example """

    def define_options(self, params):
        params.add_int("x", default=1)

    def define_jobs_context(self, context):
        options = self.get_options()
        # create a job
        context.comp(f, options.x)


def f(x):
    print("x = %s" % x)


app_example_main = AppExample.get_sys_main()

if __name__ == "__main__":
    app_example_main()
