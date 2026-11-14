---
id: workflows-aqcell
type: article
title: Predict Drug Response
gloss: AQCell predicts drug-induced gene expression and pathway activity changes after 96 hours of exposure. For every ligand × cell line pair, over a dose range, it reports dose-range endpoints (including AUC when returned by the model), how strongly requested and top-regulated genes change and which…
steps:
- name: Inputs
  detail: ligands.csv + cell_lines.csv (+ optional config.json)
  io: true
- name: predict-dose-response
  detail: AQCell drug-induced response (CPU)
- name: Results
  detail: predictions.json, result.json
  io: true
examples:
- How many drug/cell line combinations can I run at once?
- What files do I need to stage as input for aqcell predict?
- what are the defaults if I don't give a config.json?
- My config.json got rejected, what are the rules for it?
- How do I use a different config file name?
- What does the AUC in the results mean?
- Can I get IC50 or viability curves from this?
- Does the training similarity score tell me how confident the prediction is?
---
AQCell predicts drug-induced gene expression and pathway activity changes after
96 hours of exposure. For every ligand × cell line pair, over a dose range, it
reports dose-range endpoints (including AUC when returned by the model),
how strongly requested and top-regulated genes change and which
pathways respond, so that compounds can be compared before any measurement.

## When to use it

- Predict dose-dependent drug responses for every ligand × cell line pair, at
  most 32 pairs per run.
- Screen compounds by predicted expression and pathway responses in cell lines
  that the model knows.
- To train AQCell on your own dose-response measurements, use
  [`aqcell-finetune`](../aqcell-finetune/README.md); its weights can then serve
  this workflow.

## Data in

Stage `ligands.csv` with a `smiles` column and `cell_lines.csv` with a `cell_line`
column. All ligand × cell line combinations are predicted, with a maximum of
32 pairs. Use identifiers known to the selected model: these include Cellosaurus
accessions and common-name entries. Some lines have distinct expression and
viability entries; the workflow skill describes how to select them. The image validates
chemical structures and model membership for cell lines and requested genes.

An optional `config.json` in the input directory controls:

```json
{
  "genes": ["tp53", "MYC", "CDKN1A"],
  "dose_range_um": [0.01, 10.0],
  "top_genes": 10,
  "fdr_cutoff": 0.25
}
```

Omitting config uses the image defaults: no explicitly requested genes, a
0.01–10 µM dose range, 10 top up/down genes per dose, and an FDR cutoff of 0.25.
Omitted individual fields also use image defaults. The workflow rejects unknown
fields and invalid types before Nextflow's generated serializer can coerce them.
Doses must be positive and increasing; gene symbols are case-insensitive.
An optional `--config filename.json` selects another staged config basename.

The `examples/` folder of the workflow package holds a six-pair input: three
ligands, two cell lines, and a config.

## Results

Outputs are `predictions.json`, `request.json`, and `result.json`, including
resolved config, input provenance, and prediction counts. `request.json` records
the actual model request. Predictions follow the pinned AQCell contract’s
compound-major, cell-minor output order (duplicates are preserved).

At each dose of the grid, a prediction holds the expression change (logFC) of
every requested gene, the most up- and most down-regulated genes, and the
pathways whose FDR q-value stays below the cutoff. Read the returned
`pathway_set` to identify the collection. Values retain the model’s
returned precision and logFC units.

AUC, when named in `endpoint_names`, is one predicted GDSC2 area under the
response curve per pair over the requested dose range; lower means more growth
inhibition. Read `dose_ranged_endpoints` rather than deriving viability from
expression. Do not compare different dose ranges as if they were identical.
Training similarities describe coverage, not calibrated confidence, and do not
establish that both expression and viability were trained for a cell entry.

## Method

The workflow runs SandboxAQ's AQCell model, `apheris-aqcell`, on 2 CPUs, 8 GB RAM, no
accelerator. The image includes the model bundle and caches; inference
requires no network. The model predicts a grid of doses spanning
`dose_range_um`, in about 3-fold steps, assuming 96 hours of exposure.

The task uses the baked-in weights at `/opt/aqcell/weights/bundle` by default;
a fine-tuned bundle with the same layout can take its place.

Hub's response views are informed by
[Fallahi-Sichani et al. (2013)](https://pubmed.ncbi.nlm.nih.gov/24013279/) and
[Schubert et al., PROGENy (2018)](https://www.nature.com/articles/s41467-017-02391-6).

## Limits

- These are model predictions, not experimental measurements. Outputs concern
  predicted responses after 96 hours of drug exposure; do not present them as
  measured clinical response or evidence of efficacy.
- Successful execution verifies the pipeline contract; it does not establish
  scientific accuracy for a new compound or cell line.
- Results keep the model's logFC units: no viability curves or IC50 are
  derived. Pathways filtered by FDR are unreported, not zero.
- Training similarity is separate from confidence.
- A run predicts at most 32 pairs, and only for cell lines and genes the model
  knows.
