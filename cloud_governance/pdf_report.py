"""Self-contained human report from saved evidence only; no live API or evaluator."""
from io import BytesIO
from pathlib import Path
import json

from . import report_model
from xml.sax.saxutils import escape
from functools import wraps
from threading import Lock

_RENDER_LOCK = Lock()


def serialized_render(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        # ReportLab's registered TTFont objects are process-global. Keep one
        # document's subset/font state isolated from another concurrent render.
        with _RENDER_LOCK:
            return function(*args, **kwargs)
    return wrapped


def renderer_dependencies():
    try:
        import reportlab
    except ImportError as exc:
        raise RuntimeError('PDF_DEPENDENCY_MISSING') from exc
    return {'reportlab': reportlab.Version}


def readable(value):
    if value is True:
        return 'Yes (true)'
    if value is False:
        return 'No (false)'
    if value is None:
        return 'Not returned / unspecified'
    return str(value)


def inline(value):
    """Render a saved structure into one table cell without dropping a leaf."""
    if isinstance(value, (dict, list)) and value:
        return '; '.join(name + ': ' + text for name, text in flatten(value))
    return readable(value)


def flatten(value, prefix=''):
    """Preserve every observed leaf as a human-readable field/value pair."""
    if isinstance(value, dict) and value:
        for key, child in sorted(value.items()):
            yield from flatten(child, prefix + ('.' if prefix else '') + str(key))
    elif isinstance(value, list) and value:
        for i, child in enumerate(value, 1):
            yield from flatten(child, f'{prefix}[{i}]')
    else:
        yield prefix or 'Value', ('Empty object' if value == {} else 'Empty list' if value == [] else readable(value))


@serialized_render
def render_pdf(saved, generation):
    renderer_dependencies()
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle, KeepTogether
    from reportlab.platypus.tableofcontents import TableOfContents

    # ReportLab ships these licensed fonts; embed them to avoid viewer substitution.
    fonts = Path(reportlab.__file__).with_name('fonts')
    for name, filename in [('AuditSans', 'Vera.ttf'), ('AuditSans-Bold', 'VeraBd.ttf'),
                           ('AuditSans-Italic', 'VeraIt.ttf'), ('AuditSans-BoldItalic', 'VeraBI.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily('AuditSans', normal='AuditSans', bold='AuditSans-Bold',
                                  italic='AuditSans-Italic', boldItalic='AuditSans-BoldItalic')

    report, snapshot, context = saved['assessment'], saved['snapshot'], saved['context']
    program = context['program_scope']
    configuration = report_model.configuration(report)
    rows = report_model.resource_results(report)
    references = {r['id'].lower(): f'E{i:03d}' for i, r in enumerate(rows, 1)}
    raw = {r['id'].lower(): r for r in snapshot['resources']}
    sources = sorted({s['url'] for r in rows for s in r['sources']} | set(report['control_mapping']['sources']) | {r['source'] for r in (configuration['results'] if configuration else [])})
    source_ids = {url: f'S{i:02d}' for i, url in enumerate(sources, 1)}
    styles = getSampleStyleSheet()
    navy = colors.HexColor('#16334C')
    teal = colors.HexColor('#126D78')
    styles.add(ParagraphStyle(name='BodyAudit', fontName='AuditSans', fontSize=9.2, leading=12.5, spaceAfter=6, splitLongWords=1))
    styles.add(ParagraphStyle(name='SmallAudit', parent=styles['BodyAudit'], fontSize=8, leading=10.5, spaceAfter=3))
    styles.add(ParagraphStyle(name='CodeAudit', parent=styles['SmallAudit'], fontName='AuditSans', fontSize=7.5, leading=10))
    styles.add(ParagraphStyle(name='TableHeadAudit', parent=styles['SmallAudit'], textColor=colors.white, fontName='AuditSans-Bold'))
    for name in ('Heading1', 'Heading2', 'Title'):
        styles[name].fontName = 'AuditSans-Bold'
    styles['Heading3'].fontName = 'AuditSans-BoldItalic'
    styles['Heading1'].textColor = navy
    styles['Heading1'].fontSize = 17
    styles['Heading1'].leading = 21
    styles['Heading2'].textColor = teal
    styles['Title'].textColor = navy
    styles['Title'].leading = 32

    supported = set.intersection(*(set(pdfmetrics.getFont(name).face.charToGlyph) for name in
                                   ('AuditSans', 'AuditSans-Bold', 'AuditSans-Italic', 'AuditSans-BoldItalic')))

    def clean(value):
        text = readable(value)
        for mark in ('\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212'):
            text = text.replace(mark, '-')
        text = text.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
        return ''.join(c if c == '\n' or ord(c) in supported else f'[U+{ord(c):04X}]' for c in text)

    def p(value, style='BodyAudit'):
        return Paragraph(escape(clean(value)).replace('\n', '<br/>'), styles[style])

    def table(data, widths, header=True):
        formatted = [[p(v, 'TableHeadAudit' if header and i == 0 else 'SmallAudit') for v in row] for i, row in enumerate(data)]
        for i, row in enumerate(data):
            if i and isinstance(row[0], str) and row[0] in references.values():
                formatted[i][0] = Paragraph(f'<link href="#{row[0]}" color="#126D78">{row[0]}</link>', styles['SmallAudit'])
        t = LongTable(formatted, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT', splitByRow=1, splitInRow=1)
        commands = [('FONTNAME',(0,0),(-1,-1),'AuditSans'), ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),6),
                    ('RIGHTPADDING',(0,0),(-1,-1),6), ('TOPPADDING',(0,0),(-1,-1),5),
                    ('BOTTOMPADDING',(0,0),(-1,-1),5), ('LINEBELOW',(0,0),(-1,-1),0.35,colors.HexColor('#D8E1E8'))]
        if header:
            commands += [('BACKGROUND',(0,0),(-1,0),navy), ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F7F9')])]
        t.setStyle(TableStyle(commands))
        return t

    def identifier_column(values, minimum=72, maximum=175):
        """Width that keeps an identifier on one line; an assessor cites it verbatim."""
        longest = max((pdfmetrics.stringWidth(clean(value), 'AuditSans', styles['SmallAudit'].fontSize)
                       for value in values), default=0)
        return max(minimum, min(maximum, longest + 20))

    def share(remaining, ratios):
        """Split the leftover width across the remaining columns, losing nothing to rounding."""
        total = sum(ratios)
        widths = [remaining * ratio / total for ratio in ratios[:-1]]
        return widths + [remaining - sum(widths)]

    output = BytesIO()
    synthetic = report['mode'] == 'offline_fixture'
    class AuditDocument(BaseDocTemplate):
        def afterFlowable(self, flowable):
            if getattr(flowable, 'audit_bookmark', None):
                key, title = flowable.audit_bookmark
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, title, self.page, key))
                self.canv.addOutlineEntry(title, key, 0, False)
            if getattr(flowable, 'evidence_bookmark', None):
                key, title = flowable.evidence_bookmark
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(title, key, 1, False)

    doc = AuditDocument(output, initialFontName='AuditSans', pagesize=letter, rightMargin=40, leftMargin=40, topMargin=48, bottomMargin=43,
                        title='Cloud governance evidence report - ' + generation['run_id'], author='Cloud governance evidence tool',
                        subject='Saved point-in-time evidence; provisional technical assessment')
    width = letter[0] - 80
    def furniture(canvas, document):
        canvas.saveState()
        canvas.setFillColor(navy)
        canvas.setFont('AuditSans-Bold', 8)
        canvas.drawString(40, letter[1]-28, 'CLOUD GOVERNANCE  /  SAVED EVIDENCE')
        canvas.setFont('AuditSans', 7.5)
        canvas.drawRightString(letter[0]-40, letter[1]-28, 'SYNTHETIC EXAMPLE - NOT TENANT EVIDENCE' if synthetic else 'POINT-IN-TIME TECHNICAL ASSESSMENT')
        canvas.setStrokeColor(colors.HexColor('#C9D7E2'))
        canvas.line(40, 33, letter[0]-40, 33)
        canvas.setFont('AuditSans', 7)
        canvas.drawString(40, 22, generation['run_id'] + ' / ' + generation['report_id'][:14])
        canvas.drawRightString(letter[0]-40, 22, f'Page {document.page}')
        canvas.restoreState()
    doc.addPageTemplates(PageTemplate(id='audit', frames=Frame(40,43,width,letter[1]-91,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0), onPage=furniture))
    story = []
    def heading(title, key):
        h=p(title, 'Heading1');h.audit_bookmark=(key,title);story.append(h)
    def field(name, value):
        story.append(p(name + ': ' + clean(value)))

    story += [Spacer(1,25),p('Cloud governance\nEvidence assessment', 'Title'),Spacer(1,12)]
    field('Overall saved assessment', report_model.overall(report)['conclusion'])
    field('Saved resource rule conclusion',report_model.resource_summary(report)['conclusion'])
    if configuration:
        field('Saved configuration assessment conclusion', configuration['summary']['conclusion'])
        field('Configuration check counts', configuration['summary'])
    story.append(p('Evidence coverage is incomplete.' if report_model.overall(report)['coverage_incomplete'] else 'Supported collected scope satisfied; broader audit controls remain unassessed.','Heading2'))
    story += [p('One saved collection run. One self-contained auditor report. Evidence, criteria, findings and limitations are included below; access to JSON files, a database or a storage service is not needed to review the report.'),
              p('This document presents only the saved assessment. It neither recollects Azure state nor applies current rules to historical facts. Provider-managed at-rest keys are accepted. No full NIST control effectiveness or audit-period compliance conclusion is made.')]
    if synthetic:story.append(p('DEMONSTRATION ONLY. Every resource identifier and finding in this report comes from a synthetic local fixture. No Azure tenant was accessed.','Heading2'))
    for name,value in [('Collection run',generation['run_id']),('Report version',generation['report_id']),
                       ('Collection started',snapshot['started_at']),('Collection completed',snapshot['completed_at']),
                       ('Saved assessment generated',report['generated_at']),('PDF generated',generation['generated_at']),
                       ('Collector / rule / evidence schema',f"{report['tool_version']} / {report['rule_version']} / {snapshot['schema_version']}"),
                       ('PDF renderer',generation['renderer_version'])]:field(name,value)
    story.append(table([['Result','Count']]+[[s,report_model.resource_summary(report)['counts'][s]] for s in report_model.resource_summary(report)['counts']], [width*.72,width*.28]))
    story.append(PageBreak())
    heading('Document index','contents')
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle(name='AuditTOC',fontName='AuditSans',fontSize=9.2,leading=13,spaceBefore=3,splitLongWords=1)]
    story += [toc, PageBreak()]
    heading('1. Scope, methods and decision criteria','scope')
    story.append(p(report['control_mapping']['assessment']))
    field('Provisional encryption control mapping',', '.join(report['control_mapping']['controls']))
    story.append(p(context['common_criteria']))
    story.append(p('Method: read-only examination of allowlisted ARM identity/configuration and selected child/dependency metadata, plus the stated Microsoft service guarantees. No cryptographic measurement, log-content review, interview, restore exercise or incident-process test was performed. Service guarantees are scoped inferences, not direct observation of stored plaintext/ciphertext.'))
    story.append(p('PASS means the stated implemented technical criterion is met for this observed scope. FAIL means a confirmed disabling state or failed dependency. UNKNOWN means insufficient/contradictory evidence. ERROR means a required read failed. UNSUPPORTED means no reviewed exact-type rule. NOT_APPLICABLE is a documented narrow mechanism/scope exclusion. None of these statuses replaces program-wide applicability or evidence of manual/shared controls.'))
    story.append(table([['Inventory scope','Value']]+list(flatten(snapshot['inventory'])),[width*.44,width*.56]))
    for item in report['limitations']:story.append(p('- '+item))
    story.append(p('Dates cover this collection window only. Evidence age is visible, but an organization-approved freshness limit is not defined. No evidence is supplied for the rest of an audit period.'))
    provenance = context.get('execution_provenance')
    if provenance:
        story.append(table([['Saved execution provenance','Value']]+list(flatten(provenance)),[230,width-230]))
        story.append(p('The client ID records identity configuration, not independent proof of the executing principal. Live tenant validation marked arm_subscription_metadata uses authenticated ARM subscription metadata. Synthetic reports contain test context only. Tokens were not decoded or retained; storage retention policy was not verified.'))
    else:
        story.append(p('Tenant identity is not explicitly captured by this saved ARM snapshot; subscription selection and collector mode are preserved. No execution provenance extension was recorded.'))
    story.append(PageBreak())
    heading('2. Findings and evidence index','findings')
    story.append(p('Evidence references E001 onward locate the complete saved resource observations later in this document. Parent/dependency findings can describe the same underlying condition; row counts are not unique incident counts or a control pass rate.'))
    story.append(table([['Ref','Resource / ARM type','Saved status / reason']]+[
        [references[r['id'].lower()],r['name']+'\n'+r['type'],r['result']+'\n'+r['reason']] for r in rows],[45,205,width-250]))
    if not rows:story.append(p('No resource observations. Empty inventory is incomplete coverage, not an all-clear.'))
    story.append(PageBreak())
    heading('3. Wider audit applicability and missing evidence','program')
    field('Saved applicability research',program['catalog_version']+'; reviewed '+program['reviewed_on'])
    story.append(p('All 23 services remain in scope across applicable controls. Encryption findings appear in section 2. Additional saved configuration findings, when present, appear in section 8. Neither section establishes whole-control operating effectiveness. The following research context is not tenant deployment presence.'))
    story.append(table([['Domain','Evidence state in this run']]+[[d+' - '+name,'Scoped encryption results only; see E references and limitations.' if d=='R' else ('Scoped configuration evidence in section 8; provider-asserted policy results, when collected, appear in section 9. Wider objective remains incomplete.' if configuration and any(r['domain']==d for r in configuration['results']) else 'NOT COLLECTED / NOT ASSESSED. Approved criteria and scoped evidence required.')] for d,name in program['domains'].items()],[230,width-230]))
    story.append(table([['Service','Existing encryption capability / broader evidence gap']]+[[s['name'],s['current_encryption_maturity']+'. Additional saved predicates, if present, appear in section 8; wider coverage remains incomplete. '+s['shared_context']] for s in program['services']],[135,width-135]))
    story.append(p('Resource-local exclusions: private endpoints and user-assigned identities have no customer at-rest store, but retain authorization, trust, change, lifecycle, incident and governance obligations. Private endpoint approval is not proof of correct routing, DNS, target access control or disabled public access. Shared networking evidence remains with the network owner.'))
    story.append(table([['NIST family','Owner / missing shared or process evidence']]+[[f['id'].upper()+' - '+f['title'],f['responsibility']+'. NOT ASSESSED. '+f['review']] for f in program['families']],[170,width-170]))
    story.append(p('The research catalog is provisional. Organization-defined parameters have not been approved by this run. These unresolved items prevent inventing broader technical or process conclusions:'))
    story.append(table([['Code','Parameters requiring approval']]+list(program['organization_parameters'].items()),[45,width-45]))
    story.append(PageBreak())
    heading('4. Saved resource evidence','evidence')
    story.append(p('Each evidence block includes the exact saved scope, observed facts and assessment, plus child listing completeness and dependency references. Blank/empty returned metadata is identified explicitly. No current external state is used. Characters unavailable in the embedded fonts appear as explicit [U+XXXX] Unicode code points.'))
    for i,row in enumerate(rows):
        if i:story.append(PageBreak())
        ref=references[row['id'].lower()]
        h=p(ref+' | '+row['result']+' | '+row['name'],'Heading2')
        h.evidence_bookmark=(ref,ref+' - '+row['name'])
        story.append(h)
        field('Resource ID',row['id'])
        field('Type / location / SKU',row['type']+' / '+row['location']+' / '+row['sku'])
        field('Subscription / group / kind',row['subscription_id']+' / '+row['resource_group']+' / '+row['kind'])
        field('Observed / assessed',row['collected_at']+' / '+row['assessed_at'])
        field('Rule / API / evidence basis',row['rule_id']+' / '+readable(row.get('api_version'))+' / '+row['basis'])
        field('Rule scope',row['scope'])
        rule=context['rule_catalog'].get(row['type'].lower())
        mode=rule['mode'] if rule else 'unsupported'
        field('Saved criterion',context['criteria_by_mode'][mode])
        field('Saved finding',row['reason'])
        story.append(table([['Observed field','Saved value']]+list(flatten(row['evidence'])),[205,width-205]))
        original=raw[row['id'].lower()]
        field('Collection status',original['collection_status'])
        if original.get('request_path'):field('Read path',original['request_path'])
        if original['children']:
            story.append(p('Child traversal evidence','Heading3'))
            story.append(table([['Field','Saved value']]+list(flatten(original['children'])),[205,width-205]))
        for dep in row['dependencies']:
            target=references.get(str(dep['id']).lower(), 'No saved evidence reference')
            field('Dependency',f"{dep['relation']}: {target}; saved status {dep['result']}; resolved {dep['resolved']}; {dep['id']}")
        for gap in row['gaps']:field('Unresolved gap',gap)
        for err in row['errors']:field('Read error',f"{err['operation']} / {err['code']} / HTTP {err['http_status']} / {err['observed_at']}")
        field('Supporting sources',', '.join(source_ids[s['url']]+' (reviewed '+s['reviewed_on']+')' for s in row['sources']) or 'No service guarantee asserted.')
    story.append(PageBreak())
    heading('5. Collection errors and unresolved retrieval','errors')
    if report['errors']:
        for err in report['errors']:
            story.append(table([['Field','Saved error metadata']]+list(flatten(err)),[130,width-130]))
            story.append(Spacer(1,8))
    else:story.append(p('No collection errors were recorded. This does not establish complete resource, workload or audit-control coverage.'))
    story.append(PageBreak())
    heading('6. Read methods and independent verification','verification')
    story.append(p('These are saved read instructions and expected/saved observations. They were not executed during PDF generation. Auditor review of this document does not require running them. A later authorized read would retrieve current state and cannot recreate historical evidence. Synthetic commands must not be run.'))
    for row in rows:
        if not row['verification_commands']:continue
        story.append(p(references[row['id'].lower()]+' - '+row['name'],'Heading2'))
        for command in row['verification_commands']:
            story.append(p(('SYNTHETIC - DO NOT RUN. ' if command['synthetic'] else 'Authorized current-state read only. ')+command['kind']+' / '+command['relation'],'Heading3'))
            story.append(p(command['verifies']))
            story.append(p(command['command'],'CodeAudit'))
            story.append(table([['Expected / saved field','Value']]+list(flatten(command['expected_fields'])),[205,width-205]))
            story.append(p(command['interpretation']))
    story.append(PageBreak())
    heading('7. Source references and archive provenance','sources')
    story.append(p('The source statements and criteria needed for the saved conclusions are explained in this report. URLs below are optional public provenance references, not links to private evidence required to interpret a finding. Microsoft guarantees were not refreshed during report generation.'))
    for url in sources:field(source_ids[url],url)
    story.append(p('Integrity and historical association','Heading2'))
    for name,value in [('Run manifest SHA-256',saved['manifest_sha256']),('Applicability catalog SHA-256',program['catalog_sha256']),
                       ('NIST catalog version',program['nist_source']['version']),('NIST catalog SHA-256',program['nist_source']['sha256']),
                       ('PDF generation time',generation['generated_at']),('Renderer / dependency',generation['renderer_version']+' / '+json.dumps(generation['dependencies'],sort_keys=True))]:field(name,value)
    for name,item in saved['manifest']['objects'].items():field(name+' object SHA-256',item['sha256'])
    if generation.get('execution_provenance'):
        story.append(table([['PDF generation provenance','Value']]+list(flatten(generation['execution_provenance'])),[230,width-230]))
    story.append(p('The saved JSON is an internal reproducibility format: it preserves collected facts separately from evaluated conclusions. This PDF contains their human-readable substance. Hashes detect mismatch relative to the manifest; they are not signatures or proof against a privileged actor replacing an archive. The application enforces create-only publication. Local files and Azure Blob storage do not by themselves establish WORM protection or a verified retention lock. Retention duration, privileged access and immutable-storage policy remain organization-defined and were not verified by this report.'))
    if configuration:
        story.append(PageBreak())
        heading('8. Configuration control assessments','configuration')
        story.append(p(configuration['limits']))
        field('Configuration rule version', configuration['rule_version'])
        field('Saved configuration summary', configuration['summary'])
        if snapshot.get('identity_evidence'):
            graph = snapshot['identity_evidence']
            field('Graph tenant / verified / complete', {'tenant_id':graph['tenant_id'],'verified_tenant':graph['verified_tenant'],'complete':graph['complete']})
            story.append(table([['Graph collection field','Saved value']]+list(flatten(graph['listings'])),[205,width-205]))
            for identity_record in graph['resources']:
                field('Graph object / application ID', identity_record['id']+' / '+identity_record['app_id'])
                story.append(table([['Safe identity metadata','Saved value']]+list(flatten(identity_record['metadata'])),[205,width-205]))
            for error in graph['errors']:field('Graph collection error',error)
        policy = configuration['policy']
        field('Criteria identity / version / approval assertion', {k:policy[k] for k in ('id','version','status')} if policy else 'No criteria supplied')
        if policy and 'max_observation_age_seconds' in policy:
            field('Maximum observation age (seconds)',policy['max_observation_age_seconds'])
        story.append(p('Each finding below includes its saved observation and exact criterion. Missing or draft criteria do not produce PASS/FAIL. A matching property does not close the referenced research objective or establish effective authorization, private reachability, recovery or activity over time.'))
        # One predicate is one row. Rendering each as a block of labelled fields produced a
        # page per predicate and buried the findings; the same facts are tabulated instead.
        by_resource = {}
        for row in configuration['results']:
            by_resource.setdefault(row['resource_id'], []).append(row)
        check_width = identifier_column([row['check_id'] for row in configuration['results']])
        # Scope-inherited facts repeat across resources: 51 predicates in the first lab run
        # held 14 distinct observations. Printing each one once keeps every leaf and stops
        # the same role listing being reprinted per resource.
        observations, saved_texts = {}, []
        for row in configuration['results']:
            text = inline(row['observation'])
            if text not in observations:
                observations[text] = 'O%02d' % (len(observations) + 1)
                saved_texts.append(text)
        story.append(p('8.1 Saved assessments by resource','Heading2'))
        story.append(p('Each observation key resolves in 8.2. Identical observations share one key: a grant '
                       'inherited from a subscription or management group is one saved fact, not one per resource.'))
        for resource_id, group in by_resource.items():
            story.append(KeepTogether([p(resource_id,'Heading3'),
                                       p('Observed / assessment time: '
                                         + ', '.join(sorted({r['observed_at'] for r in group}))
                                         + ' / ' + configuration['generated_at'],'SmallAudit')]))
            story.append(table([['Check','Result','Property','Observation','Saved criterion','Finding']]
                               + [[r['check_id'], r['result'], r['property'], observations[inline(r['observation'])],
                                   inline(r['criterion']), r['reason']] for r in group],
                               [check_width, 56, 68] + share(width - check_width - 124, [128, 88, 142])))
        story.append(p('8.2 Saved observations','Heading2'))
        story.append(table([['Key','Saved observation as collected']]
                           + [[observations[text], text] for text in saved_texts], [44, width-44]))
        predicates = {}
        for row in configuration['results']:
            predicates.setdefault(row['check_id'], row)
        story.append(p('8.3 Predicate provenance and audit objectives','Heading2'))
        story.append(p('One entry per predicate. Read paths are the resource identifiers in 8.1 above; source '
                       'identifiers resolve in section 7. Each entry runs the full page width so a title is never '
                       'broken across a column.'))
        for check, row in predicates.items():
            story.append(p(check + ' - ' + row['title'] + '  |  objective ' + row['catalog_ref'] + ' / '
                           + row['domain'] + '  |  NIST ' + (', '.join(row.get('control_refs',[]))
                                                             or 'none declared')
                           + '  |  API ' + row['api_version'] + '  |  source '
                           + source_ids.get(row['source'], row['source']), 'SmallAudit'))
        objectives = context.get('configuration_objectives',{}).get('checks',{})
        wider = {row['catalog_ref']: objectives[row['catalog_ref']]['candidate_criterion']
                 for row in predicates.values() if row['catalog_ref'] in objectives}
        if wider:
            story.append(p('8.4 Wider candidate objectives not closed by these predicates','Heading2'))
            story.append(table([['Objective','Wider candidate criterion (not closed by the predicate)']]
                               + sorted(wider.items()), [72, width-72]))
        extra = [[row['check_id'], row['resource_id'], name, inline(row[name])]
                 for row in configuration['results']
                 for name in ('lifecycle_evaluation','job_evaluation','freshness') if name in row]
        if extra:
            story.append(p('8.5 Additional saved evaluations','Heading2'))
            story.append(table([['Check','Resource','Evaluation','Saved value']] + extra,
                               [check_width] + share(width - check_width, [170, 86, 210])))
    policy_section = report_model.policy_compliance(report)
    if policy_section:
        story.append(PageBreak())
        heading('9. Azure Policy compliance (provider asserted)','policy')
        story.append(p(policy_section['limits']))
        field('Source / assignment', policy_section['source'] + ' / ' + str(policy_section['assignment_filter']))
        field('Collected at', policy_section['collected_at'])
        field('Saved policy summary', policy_section['summary'])
        story.append(p('Microsoft evaluated these results and supplied the control mapping. This program did not '
                       'observe the configuration behind them and does not restate them as its own findings. A '
                       'resource type with no applicable definition produces no record, so the absence of a record '
                       'below is not evidence of compliance. Records evaluated at subscription or resource group '
                       'scope describe that scope and not each resource inside it.'))
        if policy_section['summary'].get('truncated'):
            story.append(p('This evaluation returned more records than the run retains. The results below are a '
                           'truncated sample; the absence of a finding in them does not mean none exists.','Heading2'))
        results = policy_section['results']
        manual = [row for row in results if str(row.get('action','')).lower() == 'manual']
        evaluated = [row for row in results if row not in manual]
        if manual:
            story.append(p('Manual definitions: recorded, not rendered as evidence','Heading2'))
            story.append(p(str(len(manual)) + ' of ' + str(len(results)) + ' records in this assignment carry the '
                           'Manual effect. A Manual definition evaluates nothing: Azure emits one record per '
                           'definition to mark a control as awaiting an organizational attestation, whatever the '
                           'subscription contains. They are retained in full in the saved JSON and are omitted from '
                           'the results below because they are not evidence about a resource. Their omission is not '
                           'a pass, and this report attests nothing on their behalf.'))
        assignments = sorted({row['assignment'] for row in evaluated})
        if assignments:
            field('Assignment recorded on every result below', ', '.join(assignments))
        story.append(p(str(len(evaluated)) + ' records evaluated a resource or a scope','Heading2'))
        # A definition reference and an evaluated resource identifier are both too wide to
        # sit in one row. The identifiers are listed once; the table carries the evidence.
        targets = {resource: 'T%02d' % index for index, resource in
                   enumerate(sorted({row['resource_id'] for row in evaluated}), 1)}
        if targets:
            story.append(table([['Target','Evaluated resource or scope identifier']]
                               + [[key, resource] for resource, key in targets.items()], [50, width-50]))
        order = {'FAIL': 0, 'UNKNOWN': 1, 'PASS': 2}
        reference_width = identifier_column([row['reference'] for row in evaluated], 120, 200)
        story.append(table([['Definition reference','Result /\ncompliance state','Effect /\nscope',
                             'Supporting NIST references','Evaluated at','Target']]
                           + [[row['reference'], row['result'] + '\n' + row['compliance_state'],
                               row['action'] + '\n' + row['scope'],
                               ', '.join(row['controls']) or 'none declared',
                               row['evaluated_at'] or 'not reported', targets[row['resource_id']]]
                              for row in sorted(evaluated, key=lambda r: (order.get(r['result'], 3),
                                                                          r['reference'], r['resource_id']))],
                           [reference_width, 69, 75] + share(width - reference_width - 186, [76, 86]) + [42]))
    doc.multiBuild(story)
    return output.getvalue()
