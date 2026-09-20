"""One reader for every saved report schema.

Reports are immutable once archived, so several shapes coexist and all of them must
stay readable exactly as written. Consumers go through these accessors instead of
indexing a report directly, so adding an evidence kind does not require every reader
to learn a new layout, and a historical run keeps rendering from its own shape.

Schema history:

* ``1.0`` — reviewed per-type rule results only, under a top-level ``results`` key.
* ``1.1`` — adds ``configuration_assessment`` nested beside them, and ``overall_summary``.
* ``1.2`` — evidence kinds become peers under ``evidence``; ``summary`` is the overall
  conclusion and ``control_mapping.controls`` is derived from the evidence actually
  collected rather than fixed to one control family.
"""

SCHEMAS = ('1.0', '1.1', '1.2')

# Every evidence kind a report may carry, in the order reports present them.
KINDS = ('resource_rules', 'configuration', 'policy_compliance')


def schema(report):
    return report.get('schema_version')


def is_current(report):
    return schema(report) == '1.2'


def resource_results(report):
    """Per-resource reviewed-rule results. Empty when a report carries none."""
    if is_current(report):
        return report.get('evidence', {}).get('resource_rules', {}).get('results', [])
    return report.get('results', [])


def resource_summary(report):
    if is_current(report):
        return report.get('evidence', {}).get('resource_rules', {}).get('summary', {})
    return report.get('summary', {})


def configuration(report):
    """The configuration predicate section, or None for a schema that predates it."""
    if is_current(report):
        return report.get('evidence', {}).get('configuration')
    return report.get('configuration_assessment')


def configuration_results(report):
    section = configuration(report)
    return section.get('results', []) if section else []


def configuration_summary(report):
    section = configuration(report)
    return section.get('summary', {}) if section else {}


def policy_compliance(report):
    """Provider-asserted policy compliance, or None when the run collected none."""
    if is_current(report):
        return report.get('evidence', {}).get('policy_compliance')
    return None


def policy_results(report):
    section = policy_compliance(report)
    return section.get('results', []) if section else []


def sections(report):
    """Present evidence kinds, as (kind, section) pairs in report order."""
    found = []
    for kind in KINDS:
        section = {'resource_rules': lambda r: {'summary': resource_summary(r), 'results': resource_results(r)},
                   'configuration': configuration,
                   'policy_compliance': policy_compliance}[kind](report)
        if section and (section.get('results') or section.get('summary')):
            found.append((kind, section))
    return found


def overall(report):
    """The cross-kind conclusion. Older reports keep their own recorded value."""
    if is_current(report):
        return report.get('summary', {})
    return report.get('overall_summary', report.get('summary', {}))
