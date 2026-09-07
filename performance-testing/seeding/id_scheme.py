"""Synthesizes functional_record_id values without the real allocation path.

Production allocates functional_record_id asynchronously: a Celery worker
calls an external HTTP id-allocation service and writes the result back
(registry-platform/.../functional_id_allocation_worker.py). That pipeline is
not reachable/scalable for a bulk load of millions of rows, so the generator
assigns ids directly, matching the same prefix scheme
(g2p_id_generator_service.py: HH- for Household, FR- for Farmer, DEFAULT-
for everything else) with a per-mnemonic sequential counter in place of the
real allocator's sequence.

For Kubernetes parallel execution, each pod is assigned a unique ID range
to prevent duplicates across pods.
"""

from config import DEFAULT_ID_PREFIX, ID_PREFIXES

_counters: dict[str, int] = {}
_pod_index: int = 0
_total_pods: int = 1
_id_range_size: int = 0


def init_pod_id_scheme(pod_index: int, total_pods: int, target_farmers: int):
    """Initialize ID scheme for a specific pod in a parallel execution.
    
    Args:
        pod_index: Zero-based index of this pod (0 to total_pods-1)
        total_pods: Total number of pods running in parallel
        target_farmers: Total number of farmers to generate across all pods
    """
    global _pod_index, _total_pods, _id_range_size, _counters
    _pod_index = pod_index
    _total_pods = total_pods
    
    # Calculate the ID range size per pod for Farmer IDs
    # We add some buffer to ensure no overlap
    _id_range_size = (target_farmers // total_pods) + 1000
    
    # Initialize counters at the starting position for this pod
    _counters = {}
    
    # For Farmer IDs, start at pod-specific offset
    _counters["Farmer"] = pod_index * _id_range_size
    
    # For Household IDs, use a different range (roughly 1/3 of farmers)
    household_range_size = _id_range_size // 3
    _counters["Household"] = pod_index * household_range_size
    
    # For other tables, use smaller ranges
    _counters["default"] = pod_index * 10000


def assign_functional_id(register_mnemonic: str) -> str:
    prefix = ID_PREFIXES.get(register_mnemonic, DEFAULT_ID_PREFIX)
    
    # Use pod-specific counter for this mnemonic
    counter_key = register_mnemonic if register_mnemonic in ID_PREFIXES else "default"
    _counters[counter_key] = _counters.get(counter_key, 0) + 1
    
    return f"{prefix}{_counters[counter_key]:09d}"
