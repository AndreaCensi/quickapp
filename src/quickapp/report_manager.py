from compmake import comp_store
from contracts import contract, describe_type, describe_value
from pprint import pformat
from quickapp import logger
from reprep import Report
from reprep.report_utils import StoreResults
from reprep.utils import frozendict2, natsorted
import os
import time

__all__ = ['ReportManager']


class ReportManager(object):
    # TODO: make it use a context
    
    def __init__(self, outdir, index_filename=None):
        self.outdir = outdir
        if index_filename is None:
            index_filename = os.path.join(self.outdir, 'report_index.html')
        self.index_filename = index_filename
        self.allreports = StoreResults()
        self.allreports_filename = StoreResults()

        # report_type -> set of keys necessary
        self._report_types_format = {}
    
    def _check_report_format(self, report_type, **kwargs):
        keys = sorted(list(kwargs.keys()))
        # print('report %r %r' % (report_type, keys))
        if not report_type in self._report_types_format:
            self._report_types_format[report_type] = keys
        else:
            keys0 = self._report_types_format[report_type]
            if not keys == keys0:
                msg = 'Report %r %r' % (report_type, keys)
                msg += '\ndoes not match previous format %r' % keys0
                raise ValueError(msg)
    
        
    @contract(report_type='str')
    def add(self, report, report_type, **kwargs):
        """
            Adds a report to the collection.
            
            :param report: Promise of a Report object
            :param report_type: A string that describes the "type" of the report
            :param kwargs:  str->str,int,float  parameters used for grouping
        """         
        if not isinstance(report_type, str):
            msg = 'Need a string for report_type, got %r.' % describe_value(report_type)
            raise ValueError(msg)
        
        from compmake import Promise
        if not isinstance(report, Promise):
            msg = ('ReportManager is mean to be given Promise objects, '
                   'which are the output of comp(). Obtained: %s' 
                   % describe_type(report))
            raise ValueError(msg)
        
        # check the format is ok
        self._check_report_format(report_type, **kwargs)
        
        key = frozendict2(report=report_type, **kwargs)
        
        if key in self.allreports:
            msg = 'Already added report for %s' % key
            msg += '\n its values is %s' % self.allreports[key]
            msg += '\n new value would be %s' % report
            raise ValueError(msg)

        self.allreports[key] = report

        dirname = os.path.join(self.outdir, report_type)
        basename = "_".join(map(str, kwargs.values()))  # XXX
        basename = basename.replace('/', '_')  # XXX
        if '/' in basename:
            raise ValueError(basename)
        filename = os.path.join(dirname, basename) 
        self.allreports_filename[key] = filename + '.html'
        
    def create_index_job(self):
        if not self.allreports:
            # no reports necessary
            return
        
        from compmake import comp
        
        # Do not pass as argument, it will take lots of memory!
        # XXX FIXME: there should be a way to make this update or not
        # otherwise new reports do not appear
        if len(self.allreports_filename) > 100:
            allreports_filename = comp_store(self.allreports_filename, 'allfilenames')
        else:
            allreports_filename = self.allreports_filename
                    
        for key in self.allreports:
            job_report = self.allreports[key]
            filename = self.allreports_filename[key] 

            write_job_id = job_report.job_id + '-write'
            
            # Create the links to reports of the same type
            report_type = key['report']
            other_reports_same_type = self.allreports_filename.select(report=report_type)
            other_reports_same_type = other_reports_same_type.remove_field('report')
            key = dict(**key)
            del key['report']
            
            comp(write_report_and_update,
                 job_report, filename, allreports_filename, self.index_filename,
                 write_pickle=True,
                 this_report=key,
                 other_reports_same_type=other_reports_same_type,
                 job_id=write_job_id)


def create_links_html(this_report, other_reports_same_type):
    '''
    :param this_report: dictionary with the keys describing the report
    :param other_reports_same_type: StoreResults -> filename
    :returns: html string describing the link
    '''
    
    s = ""

    # create table by cols
    table = create_links_html_table(this_report, other_reports_same_type)
    
    s += "<table class='variations'>"
    s += "<thead><tr>"
    for field, _ in table:
        s += "<th>%s</th>" % field
    s += "</tr></thead>"

    s += "<tr>"
    for field, variations in table:
        s += "<td>"
        for text, link in variations:
            if link is not None:
                s += "<a href='%s'> %s</a> " % (link, text)
            else:
                s += "%s " % (text)
            s += '<br/>'
            
        s += "</td>"

    s += "</tr>"
    s += "</table>"
    return s

# @contract(returns="list( tuple(str, list(tuple(str, None|str))))")
@contract(returns="list( tuple(str, *))")
def create_links_html_table(this_report, other_reports_same_type):
    # Iterate over all keys (each key gets a column)
    
    def rel_link(f):
        # TODO: make it relative
        f0 = other_reports_same_type[this_report]
        rl = os.path.relpath(f, os.path.dirname(f0))
        return rl

    cols = []
    fieldnames = other_reports_same_type.field_names()
    for field in fieldnames:
        field_values = other_reports_same_type.field_values(field)
        field_values = sorted(list(set(field_values)))
        col = []
        for fv in field_values:
            if fv == this_report[field]:
                res = ('%s (this)' % str(fv), None)
            else:
                # this is the variation obtained by changing only one field value
                variation = dict(**this_report)
                variation[field] = fv
                # if it doesn't exist:
                if not variation in other_reports_same_type:
                    res = ('%s (n/a)' % str(fv), None)
                else:
                    res = (fv, rel_link(other_reports_same_type[variation]))
            col.append(res)
        cols.append((field, col))
    return cols
    
@contract(report=Report)
def write_report_and_update(report, report_html, all_reports, index_filename,
                            this_report,
                            other_reports_same_type,
                            write_pickle=False):
    
    if not isinstance(report, Report):
        msg = 'Expected Report, got %s.' % describe_type(report)
        raise ValueError(msg) 
    
    links = create_links_html(this_report, other_reports_same_type)
    
    extras = dict(extra_html_body_start=links,
                  extra_html_body_end='<pre>%s</pre>' % report.format_tree())
    html = write_report(report, report_html, write_pickle=write_pickle, **extras)
    index_reports(reports=all_reports, index=index_filename, update=html)


@contract(report=Report, report_html='str')
def write_report(report, report_html, write_pickle=False, **kwargs): 
    from conf_tools.utils import friendly_path
    logger.debug('Writing to %r.' % friendly_path(report_html))
    if False:
        # Note here they might overwrite each other
        rd = os.path.join(os.path.dirname(report_html), 'images')
    else:
        rd = None
    report.to_html(report_html,
                   write_pickle=write_pickle, resources_dir=rd, **kwargs)
    # TODO: save hdf format
    return report_html


@contract(reports=StoreResults, index=str)
def index_reports(reports, index, update=None):  # @UnusedVariable
    """
        Writes an index for the reports to the file given. 
        The special key "report" gives the report type.
        
        reports[dict(report=...,param1=..., param2=...) ] => filename
    """
    # print('Updating because of new report %s' % update)
    from compmake.utils import duration_human
    import numpy as np
    
    dirname = os.path.dirname(index)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    # logger.info('Writing on %s' % friendly_path(index))
    
    f = open(index, 'w')
    
    f.write("""
        <html>
        <head>
        <style type="text/css">
        span.when { float: right; }
        li { clear: both; }
        a.self { color: black; text-decoration: none; }
        </style>
        </head>
        <body>
    """)
    
    mtime = lambda x: os.path.getmtime(x)
    existing = filter(lambda x: os.path.exists(x[1]), reports.items())

 
    # create order statistics
    alltimes = np.array([mtime(b) for _, b in existing]) 
    
    def order(filename):
        """ returns between 0 and 1 the order statistics """
        assert os.path.exists(filename)
        histime = mtime(filename)
        compare = (alltimes < histime) 
        return np.mean(compare * 1.0)
        
    def style_order(order):
        if order > 0.95:
            return "color: green;"
        if order > 0.9:
            return "color: orange;"        
        if order < 0.5:
            return "color: gray;"
        return ""     
        
    @contract(k=dict, filename=str)
    def write_li(k, filename, element='li'):
        desc = ",  ".join('%s = %s' % (a, b) for a, b in k.items())
        href = os.path.relpath(filename, os.path.dirname(index))
        
        if os.path.exists(filename):
            when = duration_human(time.time() - mtime(filename))
            span_when = '<span class="when">%s ago</span>' % when
            style = style_order(order(filename))
            a = '<a href="%s">%s</a>' % (href, desc)
        else:
            # print('File %s does not exist yet' % filename)
            style = ""
            span_when = '<span class="when">missing</span>'
            a = '<a href="%s">%s</a>' % (href, desc)
        f.write('<%s style="%s">%s %s</%s>' % (element, style, a, span_when,
                                               element))

        
    # write the first 10
    existing.sort(key=lambda x: (-mtime(x[1])))
    nlast = min(len(existing), 10)
    last = existing[:nlast]
    f.write('<h2 id="last">Last %d reports</h2>\n' % (nlast))

    f.write('<ul>')
    for i in range(nlast):
        write_li(*last[i])
    f.write('</ul>')

    if False:
        for report_type, r in reports.groups_by_field_value('report'):
            f.write('<h2 id="%s">%s</h2>\n' % (report_type, report_type))
            f.write('<ul>')
            r = reports.select(report=report_type)
            items = list(r.items()) 
            items.sort(key=lambda x: str(x[0]))  # XXX use natsort   
            for k, filename in items:
                write_li(k, filename)
    
            f.write('</ul>')
    
    f.write('<h2>All reports</h2>\n')

    try:
        sections = make_sections(reports)
    except:
        logger.error(str(reports.keys()))
        raise
    
    if  sections['type'] == 'sample':
        # only one...
        sections = dict(type='division', field='raw',
                          division=dict(raw1=sections), common=dict())
        
        
    def write_sections(sections, parents):
        assert 'type' in sections
        assert sections['type'] == 'division', sections
        field = sections['field']
        division = sections['division']

        f.write('<ul>')
        sorted_values = natsorted(division.keys())
        for value in sorted_values:
            parents.append(value)
            html_id = "-".join(map(str, parents))            
            bottom = division[value]
            if bottom['type'] == 'sample':
                d = {field: value}
                if not bottom['key']:
                    write_li(k=d, filename=bottom['value'], element='li')
                else:
                    f.write('<li> <p id="%s"><a class="self" href="#%s">%s = %s</a></p>\n' 
                            % (html_id, html_id, field, value))
                    f.write('<ul>')
                    write_li(k=bottom['key'], filename=bottom['value'], element='li')
                    f.write('</ul>')
                    f.write('</li>')
            else:
                f.write('<li> <p id="%s"><a class="self" href="#%s">%s = %s</a></p>\n' 
                        % (html_id, html_id, field, value))

                write_sections(bottom, parents)
                f.write('</li>')
        f.write('</ul>') 
                
    write_sections(sections, parents=[])
    
    f.write('''
    
    </body>
    </html>
    
    ''')
    f.close()


def make_sections(allruns, common=None):
    # print allruns.keys()
    if common is None:
        common = {}
        
    # print('Selecting %d with %s' % (len(allruns), common))
        
    if len(allruns) == 1:
        key = allruns.keys()[0]
        value = allruns[key]
        return dict(type='sample', common=common, key=key, value=value)
    
    fields_size = [(field, len(list(allruns.groups_by_field_value(field))))
                    for field in allruns.field_names_in_all_keys()]
        
    # Now choose the one with the least choices
    fields_size.sort(key=lambda x: x[1])
    
    if not fields_size:
        # [frozendict({'i': 1, 'n': 3}), frozendict({'i': 2, 'n': 3}), frozendict({}), frozendict({'i': 0, 'n': 3})]
        msg = 'Not all records of the same type have the same fields'
        msg += pformat(allruns.keys())
        raise ValueError(msg)
        
    field = fields_size[0][0]
    division = {}
    for value, samples in allruns.groups_by_field_value(field):
        samples = samples.remove_field(field)   
        c = dict(common)
        c[field] = value
        try:
            division[value] = make_sections(samples, common=c)
        except:
            msg = 'Error occurred inside grouping by field %r = %r' % (field, value)
            msg += '\nCommon: %r' % common
            msg += '\nSamples: %s' % list(samples.keys())
            logger.error(msg)
            raise
        
    return dict(type='division', field=field,
                division=division, common=common)

    
    