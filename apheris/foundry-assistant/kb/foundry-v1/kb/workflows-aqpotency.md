---
id: workflows-aqpotency
type: article
title: Predict Potency
gloss: SandboxAQ AQPotency scores every ligand–protein pair with a mean potency prediction, an uncertainty value, and similarity to training ligands for that protein. Use it to explore a compound panel before choosing experiments.
examples:
- What files do I need to upload to run AQPotency and what columns do they need?
- i have 3 ligands and 2 proteins, how many predictions will I get?
- Can I just give compound names like gefitinib and protein names like EGFR?
- What does the mean column in predictions.csv mean? Can I treat it as IC50 in nM?
- some rows have blank potency values. should I fill them with 0?
- What do ligand_similarity values of -1, 0 and 1 mean?
- Is there a config.json I can use to set dose, assay endpoint or units?
- How do I submit a job from the command line and track it?
---
SandboxAQ AQPotency scores every ligand–protein pair with a mean potency
prediction, an uncertainty value, and similarity to training ligands for that
protein. Use it to explore a compound panel before choosing experiments. Inputs
are molecular structures and protein accession IDs; no solved structure is needed.

## When to use it

- Compare a panel of compounds against one target, or explore a target panel
  for the same compounds.
- Review predictions together with uncertainty, training similarity, and missing
  scores to identify results that need more evidence.
- Start from public compound names or PubChem CIDs and named protein targets:
  the workflow skill resolves these into traceable structures and accessions.

For example: “Predict gefitinib and imatinib against human EGFR and KIT, and
show the scores, uncertainty, and training similarity.” This requests four
pairs. It does not specify an assay endpoint or establish experimental selectivity.
For dose-dependent expression and pathway responses in cell lines, use
[`aqcell`](../aqcell/README.md).

## Data in

Upload a directory containing these two files at its root:

```text
potency-input/
  ligands.csv
  proteins.csv
```

| File | Required column | Values |
|---|---|---|
| `ligands.csv` | `smiles` | Ligand structures, one SMILES per row |
| `proteins.csv` | `accession_id` | Protein accession IDs, one per row |

Use CSV quoting when needed. Names and CIDs must first be resolved to structures;
protein names must first be resolved to accessions with the intended species and
sequence identity. For example, UniProt identifies human EGFR as
[P00533](https://www.uniprot.org/uniprotkb/P00533/entry) and human KIT as
[P10721](https://www.uniprot.org/uniprotkb/P10721/entry). Valid UniProt identity
does not establish that a target is supported by this model.

The task trims surrounding whitespace, skips blank values, and removes exact
text duplicates while preserving first occurrence order. This is not chemical
canonicalization: two different SMILES for the same molecule may remain two
entries. Both files need at least one nonblank entry. The workload is the full
cross product of the retained ligands and proteins, not corresponding CSV rows.

### Small execution example

The package's `examples/` directory contains this six-pair input, used in the
local execution smoke test:

`ligands.csv`:

```csv
smiles
CCO
c1ccccc1
CC(=O)Oc1ccccc1C(=O)O
```

`proteins.csv`:

```csv
accession_id
P62971
P00533
```

These are execution examples, not validated positive controls or recommended
screening compounds. Use the requested compounds and targets for a real study.

### Configuration explained

| Setting | Current behavior |
|---|---|
| Scientific task config | No configurable fields; do not upload a `config.json` to change model behavior |
| Ligands and targets | Controlled by the two CSV files; every retained combination is evaluated |
| Model weights | Bundled in the selected image; this package has no external-weight input |
| Dose, exposure, assay endpoint, units | No settings for these; the workflow cannot request an IC50 assay or a dose-response curve |
| `logLevel` | Workflow logging only: `debug`, `info` (default), `warning`, `error`, or `critical`; does not change predictions |
| Input and output locations | Managed by Hub; standalone execution supplies input and output directories |

The task's resolved config is `{}`. An output `config.json` containing `{}` is
an SDK execution record, not a configuration template with hidden options.
AQCell's `dose_range_um`, `genes`, `top_genes`, and `fdr_cutoff` do not apply here.

### Start a Hub prediction

With an authenticated Apheris Foundry CLI, inspect the deployed package and
submit your prepared folder:

```sh
apheris-foundry workflows get --workflow aqpotency --json
apheris-foundry workflows run --workflow aqpotency --input ./potency-input --json
```

Use `workflows run --help` for the installed client's interface. AQPotency must
be enabled on the selected Hub. Retain the returned job ID, monitor it with
`jobs get --id <job-id>`, then download and inspect its result artifacts. The
workflow skill covers identity resolution, scientific interpretation, and
follow-up requests; the execution client's skill covers submission and retrieval.

## Results

`predictions.csv` contains one row per retained ligand–protein pair, ordered by
ligand and then protein. Join results by both identifiers, not row position.

| Column | Meaning |
|---|---|
| `accession_id`, `smiles` | Input pair identity |
| `mean` | Native model potency prediction; endpoint, units, and direction are not specified by the published contract |
| `sigma` | Returned model uncertainty; calibration and interval interpretation are not specified |
| `ligand_similarity` | Maximum count-Tanimoto similarity to training ligands paired with this protein, normally in `[0, 1]` |

Potency values can be blank when a pair cannot be featurized. Keep these missing;
do not replace them with zero or treat them as inactive compounds.

For `ligand_similarity`, `-1` means the SMILES could not be parsed by the
applicability-domain calculation. A value of `0` can mean that the protein is
absent from the training index or that no training ligand is similar; the output
does not distinguish these cases. A value of `1` is maximal fingerprint
similarity, not proof of exact molecular identity, calibrated accuracy, or an
experimental measurement. There is no validated similarity cutoff in this package.

`result.json` contains a `result` object with:

- `n_ligands`, `n_proteins`, `n_pairs`: retained input and Cartesian pair counts.
- `n_potency_dropped`: pairs dropped by potency inference, retained as blank
  potency rows in the output grid.
- `n_ad_unparseable`: pairs with unparseable applicability-domain inputs.
- `predictions_csv`: the prediction filename.

The envelope also records module identity, timestamps, and
`provenance.resolved_config`. Inspect this file and the actual CSV before
reporting success; a successful process may still have missing potency values.

A useful readout shows compound name/structure, target/species/accession, `mean`,
`sigma`, and `ligand_similarity`, plus completeness counts and the job reference.
Until the science contact confirms endpoint, units, and direction, label `mean`
as a native model score. Do not convert it to nM, label it IC50/pIC50/Kd/Ki,
interpret numerical ordering as stronger binding, or derive a confidence
interval from `sigma` alone.

## Method

The workflow runs SandboxAQ's proteochemometric model with the weights bundled
in the AQPotency 0.1.1 image; that image reports module version 0.1.0. The package
requests 2 CPUs, 10 GiB RAM (10240 MiB), and no GPU, matching the legacy Hub
Kubernetes allocation. Inference can run without network access. Public identity
lookups are a separate preparation step and need a connection or verified cache.

The applicability-domain index uses Morgan fingerprints and the maximum
count-Tanimoto similarity against training ligands for the given protein.
The six-pair example completed locally with no dropped potency pairs and no
unparseable applicability-domain pairs. This validates execution, not predictive
accuracy or capacity for larger panels; Hub queue and runtime vary.

## Limits

- Predictions are not measured assay values, evidence of clinical efficacy, or
  validated selectivity. Endpoint interpretation needs confirmation from the
  science contact before quantitative potency comparisons.
- Uncertainty and training similarity are distinct. Neither supplies a validated
  confidence threshold, and successful execution does not validate biology.
- This package publishes no target vocabulary, validated maximum panel size,
  or assurance of support for arbitrary species, isoforms, or mutations. Do not
  replace a requested variant with a canonical protein silently.
- Every ligand is paired with every protein. Large panels may need partitioning
  under the deployment's resource and cost constraints; there is no documented
  32-pair limit as in AQCell.
- The current workflow offers inference only, without configurable doses,
  exposure, assay conditions, fine-tuning, or external weights.

## Contact

Nicola, SandboxAQ (the supplied AQPotency wrapper's point of contact).
