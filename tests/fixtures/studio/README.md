# Studio publication fixture

The HTTP integration and bare Git publication journeys use the frozen stories
and reference clock in `contracts/fixtures/stories.v2.json` and
`contracts/fixtures/newsroom-status.fresh.json`. Their compatibility archive is
intentionally empty (`newspaper-data/`); current releases and their Git ancestry
are not test inputs. The production renderer, privacy checks, fourteen gates,
review state machine and bare Git transport still run unchanged.
