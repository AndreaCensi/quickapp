import os
import time
from pprint import pformat

import numpy as np
from compmake import Context, Promise
from compmake.utils import duration_compact
from conf_tools.utils import friendly_path
from contracts import contract, describe_type, describe_value
from quickapp import logger
from reprep import Report
from reprep.report_utils import StoreResults
from reprep.utils import frozendict2, natsorted

from .rm import write_report_single

__all__ = [
    'ReportManager',
]


class ReportManager(object):

    def __init__(self, context, outdir, index_filename=None):
        # TODO: remove context
        self.context = context
        self.outdir = outdir
        if index_filename is None:
            index_filename = os.path.join(self.outdir, 'report_index.html')
        self.index_filename = index_filename
        self.allreports = StoreResults()
        self.allreports_filename = StoreResults()

        # report_type -> set of keys necessary
        self._report_types_format = {}

        self.html_resources_prefix = ''

        # check if we are called more than once; would be a bug
        self.index_job_created = False

        self.static_dir = os.path.join(self.outdir, 'reprep-static')

    def merge(self, other):
        assert isinstance(other, ReportManager)
        """ Merges into this scructure the data from another reportmanager. """
        # print('I have: %d reports' % len(self.allreports))
        # print('merging with another with %d reports' % len(other.allreports))

        for key in other.allreports:
            report = other.allreports[key]

            if key in self.allreports:
                selfreport = self.allreports[key]
                msg = 'Found duplicate report %r' % key
                msg += ' jobs %s and %s' % (report, selfreport)
                # print(msg)
                if report.job_id != selfreport.job_id:
                    raise ValueError(msg)

            filename = other.allreports_filename[key]
            self.allreports[key] = report
            self.allreports_filename[key] = filename

    def set_html_resources_prefix(self, prefix):
        """ 
            Sets the prefix for the resources filename.
        
            example: set_resources_prefix('jbds')
        """
        self.html_resources_prefix = prefix + '-'

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

    def get(self, report_type, **kwargs):
        key = frozendict2(report=report_type, **kwargs)
        return self.allreports[key]

    @contract(report_type='str')
    def add(self, context, report, report_type, **kwargs):
        """
            Adds a report to the collection.
            
            :param report: Promise of a Report object
            :param report_type: A string that describes the "type" of the report
            :param kwargs:  str->str,int,float  parameters used for grouping
        """
        from quickapp.compmake_context import CompmakeContext
        assert isinstance(context, CompmakeContext)
        if not isinstance(report_type, str):
            msg = 'Need a string for report_type, got %r.' % describe_value(report_type)
            raise ValueError(msg)

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

        report_type_sane = report_type.replace('_', '')

        key_no_report = dict(**key)
        del key_no_report['report']
        basename = self.html_resources_prefix + report_type_sane
        if key_no_report:
            basename += '-' + basename_from_key(key_no_report)

        dirname = os.path.join(self.outdir, report_type_sane)
        filename = os.path.join(dirname, basename)
        self.allreports_filename[key] = filename + '.html'

        write_singles = False

        if write_singles:
            is_root = context.currently_executing == ['root']
            if not is_root:
                # Add also a single report independent of a global index

                # don't create the single report for the ones that are
                # defined in the root session

                filename_single = os.path.join(dirname, basename) + '_s.html'
                # filename_index_dyn = os.path.join(dirname, basename) + '_dyn.html'

                report_nid = self.html_resources_prefix + report_type_sane
                if key:
                    report_nid += '-' + basename_from_key(key)
                write_job_id = jobid_minus_prefix(context, report.job_id + '-writes')

                #                 write_report_yaml(report_nid, report_job_id=report.job_id,
                #                                   key=key, html_filename=filename_single,
                #                                   report_html_indexed=filename_index_dyn)

                context.comp(write_report_single,
                             report=report, report_nid=report_nid,
                             report_html=filename_single,
                             write_pickle=False,
                             static_dir=self.static_dir,
                             job_id=write_job_id)

    @contract(context=Context)
    def create_index_job(self, context):
        if self.index_job_created:
            msg = 'create_index_job() was already called once'
            raise ValueError(msg)
        self.index_job_created = True

        if not self.allreports:
            # no report necessary
            return

        create_write_jobs(context=context,
                          allreports_filename=self.allreports_filename,
                          allreports=self.allreports,
                          html_resources_prefix=self.html_resources_prefix,
                          index_filename=self.index_filename,
                          static_dir=self.static_dir,
                          suffix='write')


def create_write_jobs(context, allreports_filename, allreports,
                      html_resources_prefix, index_filename, suffix,
                      static_dir):
    # Do not pass as argument, it will take lots of memory!
    # XXX FIXME: there should be a way to make this update or not
    # otherwise new report do not appear
    optimize_space = False
    if optimize_space and len(allreports_filename) > 100:
        allreports_filename = context.comp_store(allreports_filename, 'allfilenames')
    else:
        allreports_filename = allreports_filename

    type2reports = sort_by_type(allreports_filename)

    for key in allreports:
        job_report = allreports[key]
        filename = allreports_filename[key]

        write_job_id = jobid_minus_prefix(context, job_report.job_id + '-' + suffix)

        # Create the links to report of the same type
        report_type = key['report']
        other_reports_same_type = type2reports[report_type]

        # find the closest report for different type
        others = find_others(type2reports, key)

        report_type_sane = report_type.replace('_', '')
        report_nid = html_resources_prefix + report_type_sane
        if key:
            report_nid += '-' + basename_from_key(key)

        key = dict(**key)
        del key['report']

        # XXX: not sure why this was here in the first place

        context.comp(write_report_and_update,
                     report=job_report, report_nid=report_nid,
                     report_html=filename, all_reports=allreports_filename,
                     index_filename=index_filename,
                     write_pickle=False,
                     this_report=key,
                     static_dir=static_dir,
                     other_reports_same_type=other_reports_same_type,
                     most_similar_other_type=others,
                     job_id=write_job_id)


def jobid_minus_prefix(context, want):
    prefix = context.get_comp_prefix()
    if prefix is not None:
        pref = prefix + '-'
        if want.startswith(pref):
            res = want[len(pref):]
        else:
            res = want
    else:
        res = want
    return res


def sort_by_type(allreports_filename):
    type2reports = {}
    for report_type, xs in allreports_filename.groups_by_field_value('report'):
        fields = xs.remove_field('report')
        # print(fields)
        res = StoreResults()
        for k, v in fields.items():
            res[k] = v
        type2reports[report_type] = res
    return type2reports


def find_others(type2reports, key):
    """ find the closest report for different type """
    report_type = key['report']

    key = dict(**key)
    del key['report']

    others = []
    for other_type, other_type_reports in type2reports.items():
        if other_type == report_type:
            continue
        best = get_most_similar(other_type_reports, key)
        if best is not None:
            others.append((other_type, best, other_type_reports[best]))

    return others


def get_most_similar(reports_different_type, key):
    """ Returns the report of another type that is most similar to this report. """

    def score(key1):
        v1 = set(key1.values())
        v2 = set(key.values())
        return len(v1 & v2)

    keys = list(reports_different_type.keys())
    scores = np.array(map(score, keys))

    tie = np.sum(scores == np.max(scores)) > 1
    if tie:
        # print('there is a tie: %s,\n %s' % (key, keys))
        return None

    best = keys[np.argmax(scores)]

    return best


@contract(other_reports_same_type=StoreResults)
def create_links_html(this_report, other_reports_same_type, index_filename,
                      most_similar_other_type):
    '''
    :param this_report: dictionary with the keys describing the report
    :param other_reports_same_type: StoreResults -> filename
    :returns: html string describing the link
    '''

    def rel_link(f):  # (this is FROM f0 to f) --- trust me, it's ok
        f0 = other_reports_same_type[this_report]
        rl = os.path.relpath(f, os.path.dirname(f0))
        return rl

    s = ""

    # create table by cols
    table = create_links_html_table(this_report, other_reports_same_type)

    s += "<p><a href='%s'>All report</a></p>" % rel_link(index_filename)

    s += "<table class='variations'>"
    s += "<thead><tr>"
    for field, _ in table:
        s += "<th>%s</th>" % field
    s += "</tr></thead>"

    s += "<tr>"

    add_invalid_links = True

    for field, variations in table:
        s += "<td>"

        MAX_VARIATIONS_EXPLICIT = 10

        # hide the n/a
        # variations = [v for v in variations if v[1] is not None]

        all_vars = dict(variations)
        sorted_variations = natsorted([v[0] for v in variations])
        # print('sorted: %s' % sorted_variations)
        variations = [(v, all_vars[v]) for v in sorted_variations]

        if len(variations) > MAX_VARIATIONS_EXPLICIT:
            id_select = 'select-%s' % (field)
            onchange = 'onchange_%s' % (field)
            s += "<select id='%s' onChange='%s()'>\n" % (id_select, onchange)

            for text, link in variations:
                if link is not None:
                    s += "<option value='%s'>%s</a> \n" % (link, text)
                else:
                    if add_invalid_links:
                        s += "<option value=''>%s</a> \n" % (text)
                s += '<br/>'

            s += '</select>\n'

            s += """         
<script>
    $(function(){
      // bind change event to select
      $('#%s').bind('change', function () {
          var url = $(this).val(); // get selected value
          if (url) { // require a URL
              window.location = url; // redirect
          }
          return false;
      });
    });
</script>
""" % id_select

        else:
            for text, link in variations:
                if link is not None:
                    s += "<a href='%s'> %s</a> " % (link, text)
                else:
                    if add_invalid_links:
                        s += "%s " % (text)
                s += '<br/>\n'

        s += "</td>"

    s += "</tr>"
    s += "</table>"

    #     s += '<dl>'
    #     for other_type, most_similar, filename in most_similar_other_type:
    #         s += '<dt><a href="%s">%s</a></dt><dd>%s</dd>' % (rel_link(filename),
    #                                                           other_type, most_similar)
    #     s += '</dl>'

    if most_similar_other_type:
        s += '<p>Other report: '
        for other_type, _, filename in most_similar_other_type:
            s += '<a href="%s">%s</a> ' % (rel_link(filename), other_type)
        s += '</p>'

    s = '<div style="margin-left: 1em;">' + s + '</div>'
    return s


@contract(returns="list( tuple(str, *))", other_reports_same_type=StoreResults)
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
                # res = ('<span style="font-weight:bold">%s</span>' % str(fv), None)
                res = (str(fv), None)
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


@contract(report=Report, report_nid='str', other_reports_same_type=StoreResults)
def write_report_and_update(report, report_nid, report_html, all_reports, index_filename,
                            this_report,
                            other_reports_same_type,
                            most_similar_other_type,
                            static_dir,
                            write_pickle=False):
    if not isinstance(report, Report):
        msg = 'Expected Report, got %s.' % describe_type(report)
        raise ValueError(msg)

    links = create_links_html(this_report, other_reports_same_type, index_filename,
                              most_similar_other_type=most_similar_other_type)

    tree_html = '<pre style="display:none">%s</pre>' % report.format_tree()

    extras = dict(extra_html_body_start=links,
                  extra_html_body_end=tree_html)

    report.nid = report_nid
    html = write_report(report=report,
                        report_html=report_html,
                        static_dir=static_dir,
                        write_pickle=write_pickle, **extras)
    index_reports(reports=all_reports, index=index_filename, update=html)


@contract(report=Report, report_html='str')
def write_report(report, report_html, static_dir, write_pickle=False, **kwargs):
    logger.debug('Writing to %s ' % friendly_path(report_html))
    #     if False:
    #         # Note here they might overwrite each other
    #         rd = os.path.join(os.path.dirname(report_html), 'images')
    #     else:
    rd = os.path.splitext(report_html)[0]
    report.to_html(report_html,
                   write_pickle=write_pickle,
                   resources_dir=rd,
                   static_dir=static_dir,
                   **kwargs)

    # TODO: save hdf format
    return report_html


@contract(reports=StoreResults, index=str)
def index_reports(reports, index, update=None):  # @UnusedVariable
    """
        Writes an index for the report to the file given. 
        The special key "report" gives the report type.
        
        report[dict(report=...,param1=..., param2=...) ] => filename
    """
    # print('Updating because of new report %s' % update)

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
        href = os.path.relpath(os.path.realpath(filename),
                               os.path.dirname(os.path.realpath(index)))
        if os.path.exists(filename):
            when = duration_compact(time.time() - mtime(filename))
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
    f.write('<h2 id="last">Last %d report</h2>\n' % (nlast))

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

    f.write('<h2>All report</h2>\n')

    try:
        sections = make_sections(reports)
    except:
        logger.error(str(reports.keys()))
        raise

    if sections['type'] == 'sample':
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
        except Exception:
            msg = 'Error occurred inside grouping by field %r = %r' % (field, value)
            msg += '\nCommon: %r' % common
            msg += '\nSamples: %s' % list(samples.keys())
            logger.error(msg)
            raise

    return dict(type='division', field=field,
                division=division, common=common)


def _dynreports_create_index(context, merged_data):
    rm = merged_data['report_manager']
    rm.create_index_job(context)


@contract(key=dict, returns='str')
def basename_from_key(key):
    """ Returns a nice basename from a key 
        that doesn't have special chars """
    if not key:
        raise ValueError('empty key')
    keys_ordered = sorted(key.keys())
    values = []
    for k in keys_ordered:
        value = key[k]
        value = str(value)
        value = value.replace('_', '')
        value = value.replace('-', '')
        value = value.replace('.', '')
        values.append(value)
    basename = "-".join(values)
    basename = basename.replace('/', '_')  # XXX
    return basename
