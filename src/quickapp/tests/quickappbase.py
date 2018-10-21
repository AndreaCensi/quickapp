from contracts import contract

from compmake.unittests.compmake_test import CompmakeTest
from quickapp import quickapp_main
from compmake.jobs.storage import all_jobs


class QuickappTest(CompmakeTest):
    """ Utilities for quickapp testing """

    @contract(cmd=str)
    def run_quickapp(self, qapp, cmd):
        args = ['-o', self.root0, '-c', cmd, '--compress']
        self.assertEqual(0, quickapp_main(qapp, args, sys_exit=False))

        # tell the context that it's all good
        jobs = all_jobs(self.db)        
        self.cc.reset_jobs_defined_in_this_session(jobs)
        

