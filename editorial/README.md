# Human editorial source

`pieces/<slug>/` contains a closed `fcmo-piece-v1` record, one `fcmo-essay-doc-v1` file per available locale, source and figure metadata, and language provenance. `issues/` contains curated issue manifests. The static paper build validates this tree, renders it through the production paper renderer, and copies the validated public inputs into the build artifact for the publication gate.

Drafts and review state do not belong here. Only reviewed, publication-ready content is included in a release. A pending locale renders an explicit pending page; it never falls back to another language. Retractions render a dated tombstone.
