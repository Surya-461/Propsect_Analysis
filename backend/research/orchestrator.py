from config.research_parameters import DEFAULT_RESEARCH_PARAMETERS, build_research_intents
from research.source_manager import search_all_sources
from services.entity_resolver import resolve_entity
from models.evidence import Evidence
from typing import Dict, List, Any, Optional

def build_parameters(extra_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Combines default research parameters with any proposal-specific extra parameters.
    """
    parameters = DEFAULT_RESEARCH_PARAMETERS.copy()
    if extra_parameters and isinstance(extra_parameters, dict):
        for name, config in extra_parameters.items():
            if isinstance(config, dict):
                parameters[name] = config
            elif isinstance(config, str):
                parameters[name] = {
                    "description": f"Custom research parameter for {name}",
                    "search_queries": [f'"{name}"'],
                    "preferred_sources": ["reputable_news", "company_website"]
                }
    return parameters

def research_prospect(prospect_name: str, extra_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Evidence]]:
    """
    Orchestrates multi-source research for a prospect using Canonical Entity Resolution
    and Jurisdiction-Aware Metric Research Intents.
    Returns mapping of parameter_name -> List of Evidence items.
    Optimized to return early if prospect has no matching public data.
    """
    # 1. Resolve Canonical Entity Identity (zero-key legal resolution)
    entity_profile = resolve_entity(prospect_name)
    resolved_name = entity_profile.canonical_name or prospect_name

    parameters = build_parameters(extra_parameters)
    evidence_by_parameter: Dict[str, List[Evidence]] = {}

    if not parameters:
        return evidence_by_parameter

    # Step 1: Probe primary parameter (Company Scale) first with metric intents
    first_param = list(parameters.keys())[0]
    first_config = parameters[first_param]

    if extra_parameters and first_param in extra_parameters:
        first_queries = first_config.get("search_queries", [f'"{resolved_name}" {first_param}'])
        initial_evidence = search_all_sources(
            company_name=prospect_name,
            parameter=first_param,
            search_queries=first_queries,
            preferred_sources=first_config.get("preferred_sources", [])
        )
    else:
        first_intents = build_research_intents(resolved_name, first_param, entity_profile)
        initial_evidence = search_all_sources(
            company_name=prospect_name,
            parameter=first_param,
            research_intents=first_intents,
            preferred_sources=first_config.get("preferred_sources", [])
        )

    evidence_by_parameter[first_param] = initial_evidence

    # If no valid matching evidence for primary parameter, prospect does not exist
    if not initial_evidence:
        for param_name in list(parameters.keys())[1:]:
            evidence_by_parameter[param_name] = []
        return evidence_by_parameter

    # Step 2: Continue research across remaining parameters concurrently in parallel
    import concurrent.futures

    remaining_params = list(parameters.keys())[1:]
    
    def fetch_param_evidence(p_name: str) -> tuple[str, List[Evidence]]:
        p_cfg = parameters[p_name]
        pref = p_cfg.get("preferred_sources", [])
        if extra_parameters and p_name in extra_parameters:
            q = p_cfg.get("search_queries", [f'"{resolved_name}" {p_name}'])
            items = search_all_sources(
                company_name=prospect_name,
                parameter=p_name,
                search_queries=q,
                preferred_sources=pref
            )
        else:
            ints = build_research_intents(resolved_name, p_name, entity_profile)
            items = search_all_sources(
                company_name=prospect_name,
                parameter=p_name,
                research_intents=ints,
                preferred_sources=pref
            )
        return p_name, items

    max_workers = min(6, len(remaining_params)) if remaining_params else 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_param = {executor.submit(fetch_param_evidence, p): p for p in remaining_params}
        for future in concurrent.futures.as_completed(future_to_param):
            p_name = future_to_param[future]
            try:
                p_name_res, items = future.result()
                evidence_by_parameter[p_name_res] = items
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("[ResearchOrchestrator] Parameter research failed for %s: %s", p_name, e)
                evidence_by_parameter[p_name] = []

    return evidence_by_parameter


