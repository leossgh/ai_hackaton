---
id: workflows-preprocess-structures
type: article
title: Prepare Structure Data
gloss: The workflow cleans and standardises input structures with the `apheris-data` `preprocess-structures` task. CIF or PDB structures, given directly or named by a dataset manifest, become standardised CIF files, with reports of the structures that made it through and of those that didn't, and why, so…
steps:
- name: Inputs
  detail: .cif/.pdb structures or a .json/.yaml manifest
  io: true
- name: preprocess-structures
  detail: validate, standardise, ligandize (CPU)
- name: Results
  detail: cleaned structures/ + pass/fail reports
  io: true
examples:
- What does the preprocess-structures workflow actually produce?
- I want to use a manifest instead of uploading structures one by one. What do I need to upload?
- my run finished successfully but some structures are missing from the output, why?
- What fields are in a failed entry in failed_structures.json?
- What parameters can I set and what values do they take?
- Should I turn on ignoreValidationIssues to get more structures through?
- Can I give the manifest as YAML? Any gotchas?
- How many resources does the task use, and what should I check before using the output?
---
The workflow cleans and standardises input structures with the `apheris-data`
`preprocess-structures` task. CIF or PDB structures, given directly or named by
a dataset manifest, become standardised CIF files, with reports of the
structures that made it through and of those that didn't, and why, so that
prediction or training starts from structures that passed.

## When to use it

- Standardise structures before using them in prediction or training, for
  example as the training and validation structures of
  [`structural-finetune`](../structural-finetune/README.md).
- Find out which structures of a set fail preprocessing, and why.

## Data in

Upload structure files, `.cif` or `.pdb`, directly, or a dataset manifest,
`.json`, `.yaml` or `.yml`, whose `structures` entries name them, together with
every file it names. Upload exactly one manifest when using a manifest; its
entries select the structures to process. Referenced files are not submitted
again as standalone structures. Structure and custom-component paths are
relative to the upload directory, including nested directories.

Parameters:

| Param | Values |
| --- | --- |
| `expectedFeature` | A comma-separated list of `covalent_ligand`, `bicyclic_peptide`, `peptide` and `saccharide` |
| `ligandize` | A comma-separated list of the same features |
| `ignoreValidationIssues` | `true` or `false`; the task's default is `false` |

Unset parameters leave the task's defaults in place.

YAML and JSON represent the same input fields; JSON remains supported. Provide
only one file per manifest role. YAML uses JSON scalar types: `true`, `false`,
`null` and decimal numbers; IDs such as `on` and dates remain strings. Duplicate
keys, aliases, explicit tags and multiple documents are rejected. Input fields
and constraints come from the pinned model contract, where published, and the
model task. The workflow normalizes YAML to JSON for existing task readers.

## Results

- `structures/`: the standardised CIF files.
- `result.json`: the task's result, with the number of structures, of
  successful ones and of failed ones, and its failure report.
- `successful_structures.json`: the names of the standardised structures.
- `failed_structures.json`: each failed structure with the reasons it failed.
- `structures_report.json`: every structure, the successful ones with an empty
  list of reasons.

Failed entries in both `failed_structures.json` and `structures_report.json`
include `structure` (the filename), `reasons` (the unchanged list of error
messages), `error_type` (the task's failure code), and `issues` (the task's list
of validation issue codes, which may be empty). The workflow preserves
`error_type` and `issues` as recorded by the task; each is `null` if absent in
an older failure file. Successful entries keep an empty `reasons` list and
have no failure-code fields.

## Method

The workflow runs `preprocess-structures` of `apheris-data` on 2 CPUs
with 4 GB of memory, handing it one normalized JSON manifest and its referenced
files. YAML and JSON use the same model task and validation.
From the task's result and failure report, it then writes the three structure
reports, so that callers needn't parse the task's own failure format.

## Limits

- A successful run may still contain failed structures: reconcile the input,
  successful and failed counts before using the standardised CIFs.
- Check chain, residue and ligand identities, and keep each structure's source
  provenance, before using the standardised files.
- `ignoreValidationIssues=true` relaxes validation; set it only as a deliberate
  policy.
