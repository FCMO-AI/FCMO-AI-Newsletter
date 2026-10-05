"""The only authorized bypass is the GitHub Actions App (not a human role).

App identity verified at https://api.github.com/apps/github-actions.
"""
ACTIONS_BYPASS = {'actor_id': 15368, 'actor_type': 'Integration', 'bypass_mode': 'always'}


def safe_bypass(actors):
    # Hidden/null metadata fails closed. Older rulesets with no bypass are safe
    # for human publication, but the activation plan needs the Actions exception.
    return isinstance(actors, list) and (actors == [] or actors == [ACTIONS_BYPASS])
