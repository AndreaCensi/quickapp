# from conf_tools import ConfigMaster
#  
# __all__ = ['get_conftools_rm_reports', 'get_rm_config']
#  
# class RMConfig(ConfigMaster):
#  
#     def __init__(self):
#         ConfigMaster.__init__(self, 'rm')
#         from .generated_report import GeneratedReport
#         self.reports = self.add_class_generic('report',
#                                               '*.rm_reports.yaml',
#                                               GeneratedReport)
#  
# #     def get_default_dir(self):
# #         from pkg_resources import resource_filename  # @UnresolvedImport
# #         return resource_filename("rawlogs", "configs")
#  
#  
# get_rm_config = RMConfig.get_singleton
#  
#  
# def get_conftools_rm_reports():
#     return get_rm_config().reports
#  


