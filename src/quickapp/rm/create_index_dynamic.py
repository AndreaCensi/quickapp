from contracts import contract, describe_type
from reprep import Report

__all__ = [
    'write_report_single',
]

@contract(report=Report)
def write_report_single(report,
                        report_nid, report_html,
                        static_dir,
                        write_pickle=False):
    from quickapp.report_manager import write_report

    if not isinstance(report, Report):
        msg = 'Expected Report, got %s.' % describe_type(report)
        raise ValueError(msg)
    report.nid = report_nid
    write_report(report, report_html, static_dir=static_dir, write_pickle=write_pickle)
# 
# 
# def write_report_yaml(report_nid, report_job_id, key, html_filename, report_html_indexed):
# 
#     metadata_file = os.path.splitext(html_filename)[0] + '.rm_reports.yaml'
#     rel_filename = os.path.relpath(os.path.realpath(report_html_indexed),
#                                    os.path.dirname(os.path.realpath(metadata_file)))
# 
#     entry = dict(id=report_nid, desc='Automatically generated report',
#                  code=['quickapp.rm.GeneratedReport',
#                        {'key': dict(**key),
#                         "file:filename": rel_filename,
#                         'report_job_id': report_job_id}])
#     dirname = os.path.dirname(metadata_file)
#     if not os.path.exists(dirname):
#         try:
#             os.makedirs(dirname)
#         except:
#             pass  # XXX: race condition
#     with open(metadata_file, 'w') as f:
#         f.write(yaml.dump([entry], default_flow_style=False))
# 
# # 
# def create_job_index_dynamic(context, dirname, index_filename, html_resources_prefix, static_dir):
#     """ Load the dynamically-generated report """
#     if not os.path.exists(dirname):
#         print('Reports directory not found. You should rerun this job later.')
#         return
# 
#     reports = get_conftools_rm_reports()
# 
#     print(reports.dirs_read)
#     reports.force_load(dirname)
# 
#     id_reports = list(reports.keys())
#     if not id_reports:
#         print('No report found yet.')
#         return
# 
#     allreports = StoreResults()
#     allreports_filename = StoreResults()
#     for id_report in id_reports:
#         report = reports.instance(id_report)
#         filename = report.filename
#         key = report.key
#         report_job_id = report.report_job_id
#         allreports_filename[key] = filename
#         db = context.get_compmake_db()
#         if job_exists(report_job_id, db=db):
#             allreports[key] = Promise(report_job_id)
#         else:
#             print('Warning: yaml found for job which is not there yet.')
#             print('     job: %s' % report_job_id)
# 
#     from quickapp.report_manager import create_write_jobs
#     create_write_jobs(context,
#                       allreports_filename,
#                       allreports,
#                       html_resources_prefix,
#                       index_filename,
#                       suffix='writedyn',
#                       static_dir=static_dir)
