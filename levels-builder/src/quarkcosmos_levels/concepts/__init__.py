"""
Concept registry: one plugin module per concept (concepts/<concept>.py), each
exporting CONCEPT, CODEX_KEY, DEFAULT_HANDLER, HANDLERS (obstacle type →
handler), build(difficulty) and param_space(difficulty). Adding a concept =
adding a module and one line below; nothing else is hard-coded elsewhere.
"""
from importlib import import_module

# Order = introduction order in the Quantum world (beta), see the
# gameplay-mechanics skill. "tunnel" opens the world: the most immediate
# mechanic (a threshold to clear or not, a single obstacle, obvious visual
# feedback) gets the player used to launching in a closed box without gravity
# before asking them to understand a choice of path (superposition).
ALL_CONCEPTS = ["tunnel", "superposition", "intrication", "incertitude", "quantification", "spin", "dualite"]
# Difficulties available per concept: 1 = discover (one instance of the
# mechanic), 2 = sequence (the mechanic used twice, both ways), 3 = chain
# (three instances, or two + a moving element).
DIFFICULTIES = [1, 2, 3]

_modules = {}


def concept(concept_id: str):
    """The plugin module of a concept (KeyError if unknown)."""
    if concept_id not in ALL_CONCEPTS:
        raise KeyError(concept_id)
    if concept_id not in _modules:
        _modules[concept_id] = import_module(f"{__name__}.{concept_id}")
    return _modules[concept_id]


def obstacle_handlers() -> dict:
    """Obstacle type → handler, merged over every concept (a type is owned by one concept)."""
    merged = {}
    for cid in ALL_CONCEPTS:
        for type_, handler in concept(cid).HANDLERS.items():
            assert type_ not in merged, f"obstacle type {type_!r} owned by two concepts"
            merged[type_] = handler
    return merged
