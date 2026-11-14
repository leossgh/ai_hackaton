---
id: workflows-rfd4-proteina-design
type: article
title: RFD4-Proteina design
gloss: Generate protein sequence and structure designs with RFD4-Proteina on one CUDA GPU. The workflow invokes the image's `design` task.
examples:
- Can I give RFD4-Proteina a PDB file as input?
- What fields go in a condition spec and how are structure paths resolved?
- i passed the parent folder of my yaml spec as input and it ignored my contig settings. why?
- What compute resources does a design task need?
- How should I set batchSize to avoid running out of GPU memory?
- Where do I find the generated designs after a run?
- Can I use my own fine-tuned checkpoint?
- Can I pass Hydra overrides or enable partial diffusion and refolding?
---
Generate protein sequence and structure designs with RFD4-Proteina on one CUDA GPU.
The workflow invokes the image's `design` task.

## When to use it

Use an annotated structure or upstream YAML/JSON condition spec for protein design,
including binder design or motif scaffolding. Use
[`rfd4-proteina-finetune`](../rfd4-proteina-finetune/README.md) to adapt the denoiser
before generation.

## Data in

Provide the design input and its companion structures together. A condition spec
is a mapping of design IDs to `input`, optional `input_as_annotated_cif`, `contig`
and `conditions` fields. Structure references must stay within the spec's
directory tree, using relative paths without `..`. They resolve from the spec's
directory.
Keep the spec as the entry point: passing its parent directory runs the structures
without applying the spec's instructions.

The model accepts annotated CIF/BCIF inputs, compressed CIF, and structure
directories. PDB inputs are rejected, including references inside a spec.
The included example uses upstream's annotated monomer input, preserving its
expandable chain with `input_as_annotated_cif: true`.

| Parameter | Meaning | Default |
| --- | --- | --- |
| `input` | Design spec, annotated structure, or structure directory | Required |
| `output` | Persistent result root | Required |
| `numReplicates` | Designs per input | `1` |
| `batchSize` | Generation batch size | `1` |
| `seed` | Random seed | Random |
| `checkpoint` | Uploaded flow checkpoint | Released weights in the image |
| `logLevel` | Logging verbosity: `debug`, `info`, `warning`, `error`, `critical` | `info` |

Start with batch size one for the longest input. A custom checkpoint must match
the image's model architecture and paired autoencoder.

Keep `output` and the Nextflow work directory outside the input tree so results
are not treated as input assets.
The checkpoint root is `/weights` inside the bundled image.

Each design task requests 8 CPUs, 64 GiB host RAM and 1 NVIDIA GPU.
This baseline matches the model contract; it is not a measured minimum for all
inputs. GPU VRAM is separate from host RAM and depends on input size and batch
size. Use a GPU from the [upstream supported hardware list](https://rfd4-proteina.org/latest/installation.html#supported-hardware),
start with batch size 1, and measure the longest intended input before scaling up.
The package’s DEVELOPMENT.md records sources and deployment requirements.

## Results

The task's `result.json` lists generated `*_generated.cif` structures in `designs`,
the upstream generation directory in `artifacts`, and captured output in `log`.
The bundled seed-42 example requests one design with one protein chain of 100
residues. A valid result must contain a nonempty, parseable CIF with finite atom
coordinates. These are acceptance criteria; recorded GPU results belong in the
PR validation.

Paths are relative to the task output directory. Retain the resolved configuration,
seed, image digest and checkpoint identity with the designs.

## Method

The selected Foundry module release runs RFD4-Proteina generation with
the released flow model and autoencoder; compilation is disabled. Conditions come from the
input, while the workflow exposes only the controls above. See the
[upstream cookbook](https://rfd4-proteina.org/latest/how-to/cookbook.html) and
[condition-spec guide](https://rfd4-proteina.org/latest/how-to/input_prep/yaml-json.html).

## Limits

The workflow exposes generation, without upstream search, partial-diffusion,
metric-guidance, or refolding configuration. Do not pass Hydra overrides as
workflow parameters. Design generation alone does not establish binding,
activity, stability or experimental success.

## Contact

Engineering owner: Ian Hales
Scientific owner: Leonardo Castorina

Report integration issues in the foundry-toolkit repository.
