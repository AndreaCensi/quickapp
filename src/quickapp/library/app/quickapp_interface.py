from .. import Choice, comp_comb, logger
from abc import abstractmethod, ABCMeta
from compmake import comp

__all__ = ['QuickAppInterface']


class QuickAppInterface(object):
    __metaclass__ = ABCMeta

    # Interface to be implemented
    
    @abstractmethod
    def define_options(self, params):
        """ Must be implemented """
        pass

    @abstractmethod
    def define_jobs(self):
        """ This functions should define Compmake jobs using self.comp """
        pass

    # Resources
    def get_options(self):
        return self._options

    def get_output_dir(self):
        """ Returns a suitable output directory for data files """
        return self._output_dir

    def add_report(self, report, report_type=None):
        rm = self.get_report_manager()
        logger.info('Add reports with params %s' % str(self._current_params))
        rm.add(report, report_type, **self._current_params)

    def get_report_manager(self):
        return self._report_manager
    
    # Other utility stuff
    
    @staticmethod
    def choice(it):
        return Choice(it)
    
    def comp_comb(self, *args, **kwargs):
        return comp_comb(*args, **kwargs)
    
    def comp(self, *args, **kwargs):
        """ Simple wrapper for Compmake's comp function. """
        return comp(*args, **kwargs)
