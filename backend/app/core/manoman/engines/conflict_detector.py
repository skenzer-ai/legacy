"""
Conflict Detector Engine

Identifies potential conflicts in keywords and synonyms between services
and suggests resolutions to maintain classification accuracy. This engine
ensures the service registry maintains high quality and unambiguous mappings.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

from ..models.service_registry import (
    ServiceRegistry,
    ServiceDefinition,
    ServiceOperation,
    ConflictReport,
    ConflictType,
    ConflictSeverity
)

logger = logging.getLogger(__name__)


@dataclass
class ConflictMatch:
    """Represents a specific conflict between services"""
    service1: str
    service2: str
    conflict_type: str
    conflicting_items: List[str]
    similarity_score: float
    suggested_resolution: str


class ConflictDetectorError(Exception):
    """Custom exception for conflict detection errors"""
    pass


class ConflictDetector:
    """
    Identifies potential conflicts in keywords and synonyms between services
    and suggests resolutions to maintain classification accuracy.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.detection_errors = []
        
        # Common words that shouldn't trigger conflicts
        self.common_words = {
            'get', 'post', 'put', 'delete', 'create', 'update', 'list', 'find',
            'search', 'query', 'data', 'info', 'details', 'management', 'service',
            'system', 'platform', 'api', 'endpoint', 'operation', 'request',
            'response', 'process', 'handle', 'manage', 'admin', 'user'
        }
        
        # ITSM domain synonym groups (words in same group are expected to overlap)
        self.itsm_synonym_groups = {
            'incident_group': {'incident', 'ticket', 'issue', 'problem_record'},
            'request_group': {'request', 'service_request', 'sr', 'req'},
            'change_group': {'change', 'change_request', 'cr', 'modification'},
            'problem_group': {'problem', 'problem_record', 'pr', 'root_cause'},
            'user_group': {'user', 'person', 'account', 'profile', 'individual'},
            'asset_group': {'asset', 'ci', 'configuration_item', 'device'},
            'approval_group': {'approval', 'authorize', 'review', 'validate'}
        }
    
    async def detect_conflicts_in_services(self, services: Dict[str, Any]) -> List[ConflictReport]:
        """
        Detect conflicts in a dictionary of services (temporary method for classification API)
        
        Args:
            services: Dictionary mapping service names to ServiceDefinition objects
            
        Returns:
            List of ConflictReport objects
        """
        # Create a temporary registry for conflict detection
        from ..models.service_registry import ServiceRegistry
        
        temp_registry = ServiceRegistry(
            registry_id="temp_classification",
            services=services,
            version="1.0.0",
            created_timestamp=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat()
        )
        
        return await self.detect_conflicts(temp_registry)
    
    async def detect_conflicts(self, service_registry: ServiceRegistry) -> List[ConflictReport]:
        """
        Detect conflicts in the service registry
        
        Args:
            service_registry: Complete service registry to analyze
            
        Returns:
            List of conflict reports with suggested resolutions
            
        Raises:
            ConflictDetectorError: If conflict detection fails
        """
        self.detection_errors = []
        
        try:
            logger.info(f"Starting conflict detection for {len(service_registry.services)} services")
            
            conflicts = []
            
            # 1. Check for identical keyword overlaps
            keyword_conflicts = self._detect_keyword_conflicts(service_registry.services)
            conflicts.extend(keyword_conflicts)
            
            # 2. Check for synonym conflicts
            synonym_conflicts = self._detect_synonym_conflicts(service_registry.services)
            conflicts.extend(synonym_conflicts)
            
            # 3. Check for intent verb conflicts
            intent_conflicts = self._detect_intent_conflicts(service_registry.services)
            conflicts.extend(intent_conflicts)
            
            # 4. Check for business context conflicts
            context_conflicts = self._detect_context_conflicts(service_registry.services)
            conflicts.extend(context_conflicts)
            
            # 5. Generate conflict reports
            conflict_reports = self._generate_conflict_reports(conflicts)
            
            logger.info(f"Detected {len(conflict_reports)} conflicts across {len(service_registry.services)} services")
            return conflict_reports
            
        except Exception as e:
            error_msg = f"Conflict detection failed: {str(e)}"
            self.detection_errors.append(error_msg)
            logger.error(error_msg)
            raise ConflictDetectorError(error_msg)
    
    def _detect_keyword_conflicts(self, services: Dict[str, ServiceDefinition]) -> List[ConflictMatch]:
        """Detect exact keyword matches between services"""
        conflicts = []
        
        # Build keyword to services mapping
        keyword_to_services = defaultdict(list)
        
        for service_name, service_def in services.items():
            for keyword in service_def.keywords:
                # Skip common words that are expected to overlap
                if keyword.lower() not in self.common_words:
                    keyword_to_services[keyword.lower()].append(service_name)
        
        # Find keywords used by multiple services
        for keyword, service_list in keyword_to_services.items():
            if len(service_list) > 1:
                # Check if these services should legitimately share keywords
                if not self._is_legitimate_keyword_sharing(keyword, service_list, services):
                    # Create conflict for each pair of services
                    for i in range(len(service_list)):
                        for j in range(i + 1, len(service_list)):
                            conflicts.append(ConflictMatch(
                                service1=service_list[i],
                                service2=service_list[j],
                                conflict_type="keyword_overlap",
                                conflicting_items=[keyword],
                                similarity_score=1.0,  # Exact match
                                suggested_resolution=self._suggest_keyword_resolution(keyword, service_list[i], service_list[j], services)
                            ))
        
        logger.debug(f"Found {len(conflicts)} keyword conflicts")
        return conflicts
    
    def _detect_synonym_conflicts(self, services: Dict[str, ServiceDefinition]) -> List[ConflictMatch]:
        """Detect conflicts in synonyms between services"""
        conflicts = []
        
        # Build synonym to services mapping
        synonym_to_services = defaultdict(list)
        
        for service_name, service_def in services.items():
            for synonym in service_def.synonyms:
                synonym_to_services[synonym.lower()].append(service_name)
        
        # Find synonyms used by multiple services
        for synonym, service_list in synonym_to_services.items():
            if len(service_list) > 1:
                # Check if this is legitimate (same ITSM domain)
                if not self._is_legitimate_synonym_sharing(synonym, service_list, services):
                    # Create conflict for each pair of services
                    for i in range(len(service_list)):
                        for j in range(i + 1, len(service_list)):
                            conflicts.append(ConflictMatch(
                                service1=service_list[i],
                                service2=service_list[j],
                                conflict_type="synonym_overlap",
                                conflicting_items=[synonym],
                                similarity_score=1.0,  # Exact match
                                suggested_resolution=self._suggest_synonym_resolution(synonym, service_list[i], service_list[j], services)
                            ))
        
        logger.debug(f"Found {len(conflicts)} synonym conflicts")
        return conflicts
    
    def _detect_intent_conflicts(self, services: Dict[str, ServiceDefinition]) -> List[ConflictMatch]:
        """Detect conflicts in intent verb mappings"""
        conflicts = []
        
        # Collect all intent verbs and their associated services
        verb_to_services = defaultdict(set)
        
        for service_name, service_def in services.items():
            for tier_name, tier_ops in [("tier1_operations", service_def.tier1_operations), 
                                       ("tier2_operations", service_def.tier2_operations)]:
                for operation in tier_ops.values():
                    for verb in operation.intent_verbs:
                        verb_to_services[verb.lower()].add(service_name)
        
        # Look for ambiguous verb mappings
        for verb, service_set in verb_to_services.items():
            if len(service_set) > 3:  # Verb used by many services might be ambiguous
                service_list = list(service_set)
                
                # Check if these services are related (should they share verbs?)
                unrelated_pairs = self._find_unrelated_service_pairs(service_list, services)
                
                for service1, service2 in unrelated_pairs:
                    conflicts.append(ConflictMatch(
                        service1=service1,
                        service2=service2,
                        conflict_type="intent_verb_ambiguity",
                        conflicting_items=[verb],
                        similarity_score=0.5,  # Moderate confidence
                        suggested_resolution=f"Consider using more specific verbs for '{verb}' to disambiguate between {service1} and {service2}"
                    ))
        
        logger.debug(f"Found {len(conflicts)} intent conflicts")
        return conflicts
    
    def _detect_context_conflicts(self, services: Dict[str, ServiceDefinition]) -> List[ConflictMatch]:
        """Detect conflicts in business context descriptions"""
        conflicts = []
        
        # Compare business contexts for semantic similarity
        service_names = list(services.keys())
        
        for i in range(len(service_names)):
            for j in range(i + 1, len(service_names)):
                service1_name = service_names[i]
                service2_name = service_names[j]
                
                service1 = services[service1_name]
                service2 = services[service2_name]
                
                # Calculate similarity between business contexts
                similarity = self._calculate_text_similarity(
                    service1.business_context, 
                    service2.business_context
                )
                
                if similarity >= self.similarity_threshold:
                    # High similarity might indicate these should be merged
                    conflicts.append(ConflictMatch(
                        service1=service1_name,
                        service2=service2_name,
                        conflict_type="business_context_similarity",
                        conflicting_items=[service1.business_context, service2.business_context],
                        similarity_score=similarity,
                        suggested_resolution=f"Consider merging '{service1_name}' and '{service2_name}' or refining their business contexts (similarity: {similarity:.2f})"
                    ))
        
        logger.debug(f"Found {len(conflicts)} context conflicts")
        return conflicts
    
    def _is_legitimate_keyword_sharing(self, keyword: str, service_list: List[str], services: Dict[str, ServiceDefinition]) -> bool:
        """Check if keyword sharing between services is legitimate"""
        # Check if services are in same ITSM domain
        for group_name, group_keywords in self.itsm_synonym_groups.items():
            if keyword.lower() in group_keywords:
                # Check if all services are related to this domain
                related_services = []
                for service_name in service_list:
                    service_def = services[service_name]
                    if any(sk.lower() in group_keywords for sk in service_def.keywords + service_def.synonyms):
                        related_services.append(service_name)
                
                # If most services are in the same domain, sharing is legitimate
                if len(related_services) >= len(service_list) * 0.8:
                    return True
        
        return False
    
    def _is_legitimate_synonym_sharing(self, synonym: str, service_list: List[str], services: Dict[str, ServiceDefinition]) -> bool:
        """Check if synonym sharing between services is legitimate"""
        # Same logic as keyword sharing
        return self._is_legitimate_keyword_sharing(synonym, service_list, services)
    
    def _find_unrelated_service_pairs(self, service_list: List[str], services: Dict[str, ServiceDefinition]) -> List[Tuple[str, str]]:
        """Find pairs of services that seem unrelated and shouldn't share verbs"""
        unrelated_pairs = []
        
        for i in range(len(service_list)):
            for j in range(i + 1, len(service_list)):
                service1_name = service_list[i]
                service2_name = service_list[j]
                
                service1 = services[service1_name]
                service2 = services[service2_name]
                
                # Check if services share any keywords/synonyms (indicating relatedness)
                service1_terms = set([term.lower() for term in service1.keywords + service1.synonyms])
                service2_terms = set([term.lower() for term in service2.keywords + service2.synonyms])
                
                overlap = service1_terms.intersection(service2_terms)
                
                # If no significant term overlap, they might be unrelated
                if len(overlap) < 2:  # Less than 2 shared terms
                    unrelated_pairs.append((service1_name, service2_name))
        
        return unrelated_pairs
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Simple Jaccard similarity based on words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _suggest_keyword_resolution(self, keyword: str, service1: str, service2: str, services: Dict[str, ServiceDefinition]) -> str:
        """Suggest resolution for keyword conflicts"""
        service1_def = services[service1]
        service2_def = services[service2]
        
        # Check which service uses the keyword more centrally
        service1_centrality = self._calculate_keyword_centrality(keyword, service1_def)
        service2_centrality = self._calculate_keyword_centrality(keyword, service2_def)
        
        if service1_centrality > service2_centrality:
            return f"Remove '{keyword}' from {service2} keywords (more central to {service1})"
        elif service2_centrality > service1_centrality:
            return f"Remove '{keyword}' from {service1} keywords (more central to {service2})"
        else:
            return f"Consider using more specific variations of '{keyword}' for {service1} and {service2}"
    
    def _suggest_synonym_resolution(self, synonym: str, service1: str, service2: str, services: Dict[str, ServiceDefinition]) -> str:
        """Suggest resolution for synonym conflicts"""
        # Similar logic to keyword resolution
        service1_def = services[service1]
        service2_def = services[service2]
        
        service1_centrality = self._calculate_synonym_centrality(synonym, service1_def)
        service2_centrality = self._calculate_synonym_centrality(synonym, service2_def)
        
        if service1_centrality > service2_centrality:
            return f"Remove '{synonym}' from {service2} synonyms (more relevant to {service1})"
        elif service2_centrality > service1_centrality:
            return f"Remove '{synonym}' from {service1} synonyms (more relevant to {service2})"
        else:
            return f"Consider domain-specific variants of '{synonym}' for {service1} and {service2}"
    
    def _calculate_keyword_centrality(self, keyword: str, service_def: ServiceDefinition) -> float:
        """Calculate how central a keyword is to a service definition"""
        centrality = 0.0
        
        # Check if keyword appears in service name
        if keyword.lower() in service_def.service_name.lower():
            centrality += 0.4
        
        # Check if keyword appears in description
        if keyword.lower() in service_def.service_description.lower():
            centrality += 0.3
        
        # Check if keyword appears in business context
        if keyword.lower() in service_def.business_context.lower():
            centrality += 0.2
        
        # Check frequency in keywords list
        keyword_count = service_def.keywords.count(keyword)
        if keyword_count > 0:
            centrality += 0.1 * min(keyword_count, 3)  # Cap at 0.3
        
        return centrality
    
    def _calculate_synonym_centrality(self, synonym: str, service_def: ServiceDefinition) -> float:
        """Calculate how central a synonym is to a service definition"""
        # Similar to keyword centrality but focused on synonyms
        centrality = 0.0
        
        # Check if synonym appears in service name
        if synonym.lower() in service_def.service_name.lower():
            centrality += 0.5
        
        # Check if synonym appears in descriptions
        if synonym.lower() in service_def.service_description.lower():
            centrality += 0.3
        
        # Check if synonym appears in business context
        if synonym.lower() in service_def.business_context.lower():
            centrality += 0.2
        
        return centrality
    
    def _generate_conflict_reports(self, conflicts: List[ConflictMatch]) -> List[ConflictReport]:
        """Generate structured conflict reports from detected conflicts"""
        reports = []
        
        # Group conflicts by type and severity
        conflict_groups = defaultdict(list)
        for conflict in conflicts:
            conflict_groups[conflict.conflict_type].append(conflict)
        
        for conflict_type, conflict_list in conflict_groups.items():
            # Calculate overall severity for this conflict type
            avg_similarity = sum(c.similarity_score for c in conflict_list) / len(conflict_list)
            
            if avg_similarity >= 0.9:
                severity = ConflictSeverity.HIGH
            elif avg_similarity >= 0.7:
                severity = ConflictSeverity.MEDIUM
            else:
                severity = ConflictSeverity.LOW
            
            # Map conflict type to enum
            conflict_type_enum = self._map_conflict_type(conflict_type)
            
            # Generate affected services list
            affected_services = set()
            for conflict in conflict_list:
                affected_services.add(conflict.service1)
                affected_services.add(conflict.service2)
            
            # Generate description
            description = self._generate_conflict_description(conflict_type, conflict_list)
            
            # Compile resolutions
            resolutions = [c.suggested_resolution for c in conflict_list]
            
            report = ConflictReport(
                conflict_id=f"{conflict_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                conflict_type=conflict_type_enum,
                severity=severity,
                affected_services=list(affected_services),
                description=description,
                suggested_resolutions=resolutions,
                detection_timestamp=datetime.now().isoformat(),
                auto_resolvable=self._is_auto_resolvable(conflict_type, severity)
            )
            
            reports.append(report)
        
        return reports
    
    def _map_conflict_type(self, conflict_type: str) -> ConflictType:
        """Map string conflict type to enum"""
        mapping = {
            "keyword_overlap": ConflictType.KEYWORD_OVERLAP,
            "synonym_overlap": ConflictType.SYNONYM_OVERLAP,
            "intent_verb_ambiguity": ConflictType.INTENT_AMBIGUITY,
            "business_context_similarity": ConflictType.BUSINESS_CONTEXT_OVERLAP
        }
        return mapping.get(conflict_type, ConflictType.UNKNOWN)
    
    def _generate_conflict_description(self, conflict_type: str, conflicts: List[ConflictMatch]) -> str:
        """Generate human-readable description for conflict group"""
        conflict_count = len(conflicts)
        unique_services = set()
        for conflict in conflicts:
            unique_services.add(conflict.service1)
            unique_services.add(conflict.service2)
        
        service_count = len(unique_services)
        
        descriptions = {
            "keyword_overlap": f"Found {conflict_count} keyword overlaps affecting {service_count} services",
            "synonym_overlap": f"Found {conflict_count} synonym overlaps affecting {service_count} services", 
            "intent_verb_ambiguity": f"Found {conflict_count} ambiguous intent verbs affecting {service_count} services",
            "business_context_similarity": f"Found {conflict_count} services with highly similar business contexts"
        }
        
        return descriptions.get(conflict_type, f"Found {conflict_count} conflicts of type {conflict_type}")
    
    def _is_auto_resolvable(self, conflict_type: str, severity: ConflictSeverity) -> bool:
        """Determine if conflict can be automatically resolved"""
        # Only low-severity keyword/synonym conflicts can be auto-resolved
        auto_resolvable_types = {"keyword_overlap", "synonym_overlap"}
        return conflict_type in auto_resolvable_types and severity == ConflictSeverity.LOW
    
    def get_detection_errors(self) -> List[str]:
        """Get list of detection errors encountered"""
        return self.detection_errors.copy()
    
    def get_conflict_statistics(self, conflict_reports: List[ConflictReport]) -> Dict[str, Any]:
        """Get statistics about detected conflicts"""
        if not conflict_reports:
            return {}
        
        # Count by type
        type_counts = Counter(report.conflict_type.value for report in conflict_reports)
        
        # Count by severity
        severity_counts = Counter(report.severity.value for report in conflict_reports)
        
        # Count auto-resolvable
        auto_resolvable = sum(1 for report in conflict_reports if report.auto_resolvable)
        
        # Count affected services
        all_affected = set()
        for report in conflict_reports:
            all_affected.update(report.affected_services)
        
        return {
            "total_conflicts": len(conflict_reports),
            "conflict_types": dict(type_counts),
            "severity_distribution": dict(severity_counts),
            "auto_resolvable": auto_resolvable,
            "manual_resolution_required": len(conflict_reports) - auto_resolvable,
            "affected_services": len(all_affected),
            "detection_errors": len(self.detection_errors)
        }