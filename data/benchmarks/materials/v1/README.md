# Material Benchmark v1

This directory defines the versioned contract for the first APEX Vision AI material benchmark fixture.

## Purpose

The benchmark is intentionally small and deterministic for CI regression testing. It is **not** a claim of real-world model accuracy.

Production accuracy must be measured against representative, labelled images that are separated into development and held-out test sets.

## Record contract

Each benchmark record should contain:

- `id`: stable unique identifier
- `image`: relative path to the source image
- `material`: ground-truth material label
- `finish`: optional ground-truth finish label
- `split`: `train`, `validation`, or `test`
- `source`: provenance/reference for the sample

Allowed material labels for v1:

- `ceramic`
- `stone`
- `wood`
- `vinyl`
- `carpet`

Allowed finish labels:

- `matte`
- `satin`
- `gloss`

## Dataset governance

Do not commit customer images, personal data, copyrighted images without permission, or synthetic samples presented as real-world evidence.

Every production benchmark release must record dataset version, sample count, label distribution, provenance, and evaluation date.
