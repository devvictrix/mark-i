"""
Advanced Knowledge Organization System for MARK-I Knowledge Base.

This module provides sophisticated knowledge graph organization, relationship mapping,
and knowledge consolidation capabilities that go beyond basic storage to include
semantic understanding, pattern recognition, and intelligent knowledge structuring.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import json
import os
import networkx as nx
import numpy as np

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context, ExecutionResult
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".knowledge.knowledge_organizer")


class RelationshipType(Enum):
    """Types of relationships between knowledge entities."""

    CAUSAL = "causal"  # A causes B
    TEMPORAL = "temporal"  # A happens before/after B
    HIERARCHICAL = "hierarchical"  # A is parent/child of B
    ASSOCIATIVE = "associative"  # A is related to B
    FUNCTIONAL = "functional"  # A performs function for B
    CONTEXTUAL = "contextual"  # A appears in context of B
    SIMILARITY = "similarity"  # A is similar to B
    DEPENDENCY = "dependency"  # A depends on B


class KnowledgeEntityType(Enum):
    """Types of knowledge entities."""

    CONCEPT = "concept"
    ACTION = "action"
    APPLICATION = "application"
    USER_PREFERENCE = "user_preference"
    WORKFLOW = "workflow"
    PATTERN = "pattern"
    INSIGHT = "insight"
    EXPERIENCE = "experience"


@dataclass
class KnowledgeEntity:
    """Represents a knowledge entity in the knowledge graph."""

    entity_id: str
    entity_type: KnowledgeEntityType
    name: str
    properties: Dict[str, Any]
    importance_score: float
    creation_time: datetime
    last_accessed: datetime
    access_count: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class KnowledgeRelationship:
    """Represents a relationship between knowledge entities."""

    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: RelationshipType
    strength: float
    confidence: float
    evidence: List[Dict[str, Any]]
    created_at: datetime
    last_reinforced: datetime


@dataclass
class KnowledgeCluster:
    """Represents a cluster of related knowledge entities."""

    cluster_id: str
    name: str
    entities: List[str]  # entity IDs
    central_concepts: List[str]
    cluster_strength: float
    coherence_score: float
    created_at: datetime


class AdvancedKnowledgeOrganizer(ProcessingComponent):
    """
    Advanced knowledge organization system.

    Provides sophisticated knowledge graph organization, relationship mapping,
    and knowledge consolidation with semantic understanding and pattern recognition.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)

        # Configuration
        self.max_entities = getattr(config, "max_entities", 50000)
        self.relationship_threshold = getattr(config, "relationship_threshold", 0.6)
        self.cluster_coherence_threshold = getattr(config, "cluster_coherence_threshold", 0.7)
        self.consolidation_interval = getattr(config, "consolidation_interval", 1000)
        self.importance_decay_rate = getattr(config, "importance_decay_rate", 0.02)

        # Data structures
        self.knowledge_entities: Dict[str, KnowledgeEntity] = {}
        self.knowledge_relationships: Dict[str, KnowledgeRelationship] = {}
        self.knowledge_clusters: Dict[str, KnowledgeCluster] = {}
        self.knowledge_graph = nx.DiGraph()

        # Indices for efficient access
        self.entity_type_index: Dict[KnowledgeEntityType, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.temporal_index: Dict[str, List[str]] = defaultdict(list)  # date -> entity_ids

        # Threading
        self.organization_lock = threading.Lock()
        self.graph_lock = threading.Lock()

        # Consolidation tracking
        self.operations_since_consolidation = 0

        # Load existing data
        self._load_organization_data()

        logger.info("AdvancedKnowledgeOrganizer initialized")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this knowledge organizer."""
        return {
            "knowledge_graph_organization": True,
            "relationship_mapping": True,
            "semantic_clustering": True,
            "pattern_recognition": True,
            "knowledge_consolidation": True,
            "importance_scoring": True,
            "temporal_organization": True,
            "multi_dimensional_indexing": True,
        }

    def add_knowledge_entity(self, entity_data: Dict[str, Any]) -> str:
        """Add a new knowledge entity to the organization system."""
        try:
            with self.organization_lock:
                entity_id = entity_data.get("entity_id") or f"entity_{int(time.time())}_{hash(str(entity_data))}"

                entity = KnowledgeEntity(
                    entity_id=entity_id,
                    entity_type=KnowledgeEntityType(entity_data.get("entity_type", "concept")),
                    name=entity_data.get("name", "Unknown"),
                    properties=entity_data.get("properties", {}),
                    importance_score=entity_data.get("importance_score", 0.5),
                    creation_time=datetime.now(),
                    last_accessed=datetime.now(),
                    tags=entity_data.get("tags", []),
                )

                # Store entity
                self.knowledge_entities[entity_id] = entity

                # Update indices
                self.entity_type_index[entity.entity_type].add(entity_id)
                for tag in entity.tags:
                    self.tag_index[tag].add(entity_id)

                date_key = entity.creation_time.strftime("%Y-%m-%d")
                self.temporal_index[date_key].append(entity_id)

                # Add to graph
                with self.graph_lock:
                    self.knowledge_graph.add_node(entity_id, **entity.properties)

                # Trigger consolidation if needed
                self.operations_since_consolidation += 1
                if self.operations_since_consolidation >= self.consolidation_interval:
                    self._consolidate_knowledge()

                logger.debug(f"Added knowledge entity: {entity_id}")
                return entity_id

        except Exception as e:
            logger.error(f"Error adding knowledge entity: {e}")
            return ""

    def add_relationship(self, relationship_data: Dict[str, Any]) -> str:
        """Add a relationship between knowledge entities."""
        try:
            with self.organization_lock:
                source_id = relationship_data.get("source_entity_id")
                target_id = relationship_data.get("target_entity_id")

                if not source_id or not target_id:
                    logger.warning("Invalid relationship data: missing entity IDs")
                    return ""

                if source_id not in self.knowledge_entities or target_id not in self.knowledge_entities:
                    logger.warning("Invalid relationship: one or both entities don't exist")
                    return ""

                relationship_id = f"rel_{source_id}_{target_id}_{int(time.time())}"

                relationship = KnowledgeRelationship(
                    relationship_id=relationship_id,
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relationship_type=RelationshipType(relationship_data.get("relationship_type", "associative")),
                    strength=relationship_data.get("strength", 0.5),
                    confidence=relationship_data.get("confidence", 0.5),
                    evidence=relationship_data.get("evidence", []),
                    created_at=datetime.now(),
                    last_reinforced=datetime.now(),
                )

                # Store relationship
                self.knowledge_relationships[relationship_id] = relationship

                # Add to graph
                with self.graph_lock:
                    self.knowledge_graph.add_edge(source_id, target_id, relationship_type=relationship.relationship_type.value, strength=relationship.strength, confidence=relationship.confidence)

                logger.debug(f"Added relationship: {relationship_id}")
                return relationship_id

        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return ""

    def discover_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Discover potential relationships for an entity."""
        try:
            if entity_id not in self.knowledge_entities:
                return []

            entity = self.knowledge_entities[entity_id]
            discovered_relationships = []

            # Find entities with similar properties
            similar_entities = self._find_similar_entities(entity)

            for similar_id, similarity_score in similar_entities:
                if similarity_score > self.relationship_threshold:
                    discovered_relationships.append(
                        {
                            "target_entity_id": similar_id,
                            "relationship_type": RelationshipType.SIMILARITY.value,
                            "strength": similarity_score,
                            "confidence": similarity_score * 0.8,
                            "evidence": [{"type": "property_similarity", "score": similarity_score}],
                        }
                    )

            # Find temporal relationships
            temporal_relationships = self._find_temporal_relationships(entity)
            discovered_relationships.extend(temporal_relationships)

            # Find contextual relationships
            contextual_relationships = self._find_contextual_relationships(entity)
            discovered_relationships.extend(contextual_relationships)

            return discovered_relationships

        except Exception as e:
            logger.error(f"Error discovering relationships: {e}")
            return []

    def _find_similar_entities(self, entity: KnowledgeEntity) -> List[Tuple[str, float]]:
        """Find entities similar to the given entity."""
        similar_entities = []

        for other_id, other_entity in self.knowledge_entities.items():
            if other_id == entity.entity_id:
                continue

            # Calculate similarity based on properties and tags
            similarity = self._calculate_entity_similarity(entity, other_entity)

            if similarity > 0.3:  # Minimum similarity threshold
                similar_entities.append((other_id, similarity))

        # Sort by similarity
        similar_entities.sort(key=lambda x: x[1], reverse=True)
        return similar_entities[:10]  # Return top 10

    def _calculate_entity_similarity(self, entity1: KnowledgeEntity, entity2: KnowledgeEntity) -> float:
        """Calculate similarity between two entities."""
        similarity = 0.0

        # Type similarity
        if entity1.entity_type == entity2.entity_type:
            similarity += 0.3

        # Tag similarity
        tags1 = set(entity1.tags)
        tags2 = set(entity2.tags)
        if tags1 and tags2:
            tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            similarity += tag_similarity * 0.4

        # Property similarity
        props1 = entity1.properties
        props2 = entity2.properties

        common_keys = set(props1.keys()).intersection(set(props2.keys()))
        if common_keys:
            prop_matches = sum(1 for key in common_keys if props1[key] == props2[key])
            prop_similarity = prop_matches / len(common_keys)
            similarity += prop_similarity * 0.3

        return min(1.0, similarity)

    def _find_temporal_relationships(self, entity: KnowledgeEntity) -> List[Dict[str, Any]]:
        """Find temporal relationships for an entity."""
        temporal_relationships = []

        # Find entities created around the same time
        entity_date = entity.creation_time.strftime("%Y-%m-%d")

        # Check entities from same day and adjacent days
        for days_offset in [-1, 0, 1]:
            check_date = (entity.creation_time + timedelta(days=days_offset)).strftime("%Y-%m-%d")

            if check_date in self.temporal_index:
                for other_id in self.temporal_index[check_date]:
                    if other_id != entity.entity_id:
                        other_entity = self.knowledge_entities[other_id]

                        # Determine temporal relationship
                        if other_entity.creation_time < entity.creation_time:
                            relationship_type = RelationshipType.TEMPORAL
                            strength = 0.6
                        elif other_entity.creation_time > entity.creation_time:
                            relationship_type = RelationshipType.TEMPORAL
                            strength = 0.6
                        else:
                            relationship_type = RelationshipType.CONTEXTUAL
                            strength = 0.7

                        temporal_relationships.append(
                            {
                                "target_entity_id": other_id,
                                "relationship_type": relationship_type.value,
                                "strength": strength,
                                "confidence": 0.7,
                                "evidence": [{"type": "temporal_proximity", "time_diff": abs((other_entity.creation_time - entity.creation_time).total_seconds())}],
                            }
                        )

        return temporal_relationships[:5]  # Limit to 5 temporal relationships

    def _find_contextual_relationships(self, entity: KnowledgeEntity) -> List[Dict[str, Any]]:
        """Find contextual relationships for an entity."""
        contextual_relationships = []

        # Find entities that share context (e.g., same application, workflow)
        entity_context = entity.properties.get("context", {})

        if entity_context:
            for other_id, other_entity in self.knowledge_entities.items():
                if other_id == entity.entity_id:
                    continue

                other_context = other_entity.properties.get("context", {})

                # Check for context overlap
                context_overlap = self._calculate_context_overlap(entity_context, other_context)

                if context_overlap > 0.5:
                    contextual_relationships.append(
                        {
                            "target_entity_id": other_id,
                            "relationship_type": RelationshipType.CONTEXTUAL.value,
                            "strength": context_overlap,
                            "confidence": context_overlap * 0.9,
                            "evidence": [{"type": "context_overlap", "overlap_score": context_overlap}],
                        }
                    )

        return contextual_relationships[:5]  # Limit to 5 contextual relationships

    def _calculate_context_overlap(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate overlap between two contexts."""
        if not context1 or not context2:
            return 0.0

        overlap = 0.0
        total_keys = set(context1.keys()).union(set(context2.keys()))

        for key in total_keys:
            if key in context1 and key in context2:
                if context1[key] == context2[key]:
                    overlap += 1.0
                elif str(context1[key]).lower() in str(context2[key]).lower() or str(context2[key]).lower() in str(context1[key]).lower():
                    overlap += 0.5

        return overlap / len(total_keys) if total_keys else 0.0

    def create_knowledge_clusters(self) -> Dict[str, KnowledgeCluster]:
        """Create clusters of related knowledge entities."""
        try:
            with self.organization_lock:
                clusters = {}

                # Use community detection on the knowledge graph
                if len(self.knowledge_graph.nodes()) > 3:
                    # Convert to undirected graph for community detection
                    undirected_graph = self.knowledge_graph.to_undirected()

                    # Simple clustering based on connected components
                    connected_components = list(nx.connected_components(undirected_graph))

                    for i, component in enumerate(connected_components):
                        if len(component) >= 2:  # Only create clusters with multiple entities
                            cluster_id = f"cluster_{i}_{int(time.time())}"

                            # Calculate cluster properties
                            central_concepts = self._identify_central_concepts(component)
                            cluster_strength = self._calculate_cluster_strength(component)
                            coherence_score = self._calculate_cluster_coherence(component)

                            cluster = KnowledgeCluster(
                                cluster_id=cluster_id,
                                name=f"Cluster_{i}",
                                entities=list(component),
                                central_concepts=central_concepts,
                                cluster_strength=cluster_strength,
                                coherence_score=coherence_score,
                                created_at=datetime.now(),
                            )

                            clusters[cluster_id] = cluster

                self.knowledge_clusters = clusters
                logger.info(f"Created {len(clusters)} knowledge clusters")
                return clusters

        except Exception as e:
            logger.error(f"Error creating knowledge clusters: {e}")
            return {}

    def _identify_central_concepts(self, entity_ids: Set[str]) -> List[str]:
        """Identify central concepts in a cluster."""
        central_concepts = []

        # Calculate centrality for each entity in the cluster
        subgraph = self.knowledge_graph.subgraph(entity_ids)

        if len(subgraph.nodes()) > 1:
            try:
                centrality = nx.degree_centrality(subgraph)

                # Sort by centrality and take top concepts
                sorted_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

                for entity_id, centrality_score in sorted_entities[:3]:  # Top 3
                    if entity_id in self.knowledge_entities:
                        entity = self.knowledge_entities[entity_id]
                        central_concepts.append(entity.name)

            except Exception as e:
                logger.debug(f"Error calculating centrality: {e}")

        return central_concepts

    def _calculate_cluster_strength(self, entity_ids: Set[str]) -> float:
        """Calculate the strength of connections within a cluster."""
        if len(entity_ids) < 2:
            return 0.0

        total_strength = 0.0
        connection_count = 0

        for relationship in self.knowledge_relationships.values():
            if relationship.source_entity_id in entity_ids and relationship.target_entity_id in entity_ids:
                total_strength += relationship.strength
                connection_count += 1

        return total_strength / max(1, connection_count)

    def _calculate_cluster_coherence(self, entity_ids: Set[str]) -> float:
        """Calculate how coherent a cluster is."""
        if len(entity_ids) < 2:
            return 0.0

        # Calculate coherence based on entity type consistency and tag overlap
        entity_types = []
        all_tags = []

        for entity_id in entity_ids:
            if entity_id in self.knowledge_entities:
                entity = self.knowledge_entities[entity_id]
                entity_types.append(entity.entity_type)
                all_tags.extend(entity.tags)

        # Type coherence
        type_counter = Counter(entity_types)
        most_common_type_count = type_counter.most_common(1)[0][1] if type_counter else 0
        type_coherence = most_common_type_count / len(entity_ids)

        # Tag coherence
        tag_counter = Counter(all_tags)
        shared_tags = sum(1 for count in tag_counter.values() if count > 1)
        tag_coherence = shared_tags / max(1, len(set(all_tags)))

        return (type_coherence + tag_coherence) / 2.0

    def get_knowledge_graph_structure(self) -> Dict[str, Any]:
        """Get the structure of the knowledge graph."""
        try:
            with self.graph_lock:
                structure = {
                    "nodes": [],
                    "edges": [],
                    "clusters": [],
                    "statistics": {
                        "total_entities": len(self.knowledge_entities),
                        "total_relationships": len(self.knowledge_relationships),
                        "total_clusters": len(self.knowledge_clusters),
                        "graph_density": nx.density(self.knowledge_graph) if self.knowledge_graph.nodes() else 0.0,
                    },
                }

                # Add nodes
                for entity_id, entity in self.knowledge_entities.items():
                    node = {"id": entity_id, "name": entity.name, "type": entity.entity_type.value, "importance": entity.importance_score, "access_count": entity.access_count, "tags": entity.tags}
                    structure["nodes"].append(node)

                # Add edges
                for relationship_id, relationship in self.knowledge_relationships.items():
                    edge = {
                        "id": relationship_id,
                        "source": relationship.source_entity_id,
                        "target": relationship.target_entity_id,
                        "type": relationship.relationship_type.value,
                        "strength": relationship.strength,
                        "confidence": relationship.confidence,
                    }
                    structure["edges"].append(edge)

                # Add clusters
                for cluster_id, cluster in self.knowledge_clusters.items():
                    cluster_info = {
                        "id": cluster_id,
                        "name": cluster.name,
                        "entities": cluster.entities,
                        "central_concepts": cluster.central_concepts,
                        "strength": cluster.cluster_strength,
                        "coherence": cluster.coherence_score,
                    }
                    structure["clusters"].append(cluster_info)

                return structure

        except Exception as e:
            logger.error(f"Error getting knowledge graph structure: {e}")
            return {"nodes": [], "edges": [], "clusters": [], "statistics": {}}

    def consolidate_knowledge(self) -> Dict[str, Any]:
        """Consolidate and optimize the knowledge organization."""
        return self._consolidate_knowledge()

    def _consolidate_knowledge(self) -> Dict[str, Any]:
        """Internal knowledge consolidation process."""
        try:
            consolidation_results = {"entities_processed": 0, "relationships_processed": 0, "clusters_created": 0, "duplicates_merged": 0, "weak_relationships_removed": 0}

            logger.info("Starting knowledge consolidation")

            # Remove weak relationships
            weak_relationships = []
            for rel_id, relationship in self.knowledge_relationships.items():
                if relationship.strength < 0.3 and relationship.confidence < 0.4:
                    weak_relationships.append(rel_id)

            for rel_id in weak_relationships:
                del self.knowledge_relationships[rel_id]
                if self.knowledge_graph.has_edge(self.knowledge_relationships[rel_id].source_entity_id, self.knowledge_relationships[rel_id].target_entity_id):
                    self.knowledge_graph.remove_edge(self.knowledge_relationships[rel_id].source_entity_id, self.knowledge_relationships[rel_id].target_entity_id)

            consolidation_results["weak_relationships_removed"] = len(weak_relationships)

            # Merge duplicate entities
            duplicates_merged = self._merge_duplicate_entities()
            consolidation_results["duplicates_merged"] = duplicates_merged

            # Update importance scores
            self._update_importance_scores()
            consolidation_results["entities_processed"] = len(self.knowledge_entities)

            # Create/update clusters
            clusters = self.create_knowledge_clusters()
            consolidation_results["clusters_created"] = len(clusters)

            # Reset consolidation counter
            self.operations_since_consolidation = 0

            logger.info(f"Knowledge consolidation completed: {consolidation_results}")
            return consolidation_results

        except Exception as e:
            logger.error(f"Error during knowledge consolidation: {e}")
            return {"error": str(e)}

    def _merge_duplicate_entities(self) -> int:
        """Merge entities that appear to be duplicates."""
        duplicates_merged = 0

        # Find potential duplicates based on name and properties
        entity_groups = defaultdict(list)

        for entity_id, entity in self.knowledge_entities.items():
            # Group by name and type
            key = (entity.name.lower(), entity.entity_type)
            entity_groups[key].append(entity_id)

        # Merge groups with multiple entities
        for group in entity_groups.values():
            if len(group) > 1:
                # Keep the entity with highest importance score
                entities = [(eid, self.knowledge_entities[eid]) for eid in group]
                entities.sort(key=lambda x: x[1].importance_score, reverse=True)

                primary_entity_id = entities[0][0]
                primary_entity = entities[0][1]

                # Merge properties and relationships from other entities
                for entity_id, entity in entities[1:]:
                    # Merge properties
                    for key, value in entity.properties.items():
                        if key not in primary_entity.properties:
                            primary_entity.properties[key] = value

                    # Merge tags
                    for tag in entity.tags:
                        if tag not in primary_entity.tags:
                            primary_entity.tags.append(tag)

                    # Update relationships to point to primary entity
                    for rel_id, relationship in self.knowledge_relationships.items():
                        if relationship.source_entity_id == entity_id:
                            relationship.source_entity_id = primary_entity_id
                        if relationship.target_entity_id == entity_id:
                            relationship.target_entity_id = primary_entity_id

                    # Remove duplicate entity
                    del self.knowledge_entities[entity_id]
                    if self.knowledge_graph.has_node(entity_id):
                        self.knowledge_graph.remove_node(entity_id)

                    duplicates_merged += 1

        return duplicates_merged

    def _update_importance_scores(self):
        """Update importance scores for all entities."""
        current_time = datetime.now()

        for entity in self.knowledge_entities.values():
            # Apply time decay
            days_since_access = (current_time - entity.last_accessed).days
            decay_factor = max(0.1, 1.0 - (days_since_access * self.importance_decay_rate))

            # Calculate new importance based on access count and relationships
            relationship_count = sum(1 for rel in self.knowledge_relationships.values() if rel.source_entity_id == entity.entity_id or rel.target_entity_id == entity.entity_id)

            access_score = min(1.0, entity.access_count / 100.0)
            relationship_score = min(1.0, relationship_count / 10.0)

            entity.importance_score = (access_score * 0.4 + relationship_score * 0.4 + entity.importance_score * 0.2) * decay_factor

    def search_knowledge(self, query: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for knowledge entities based on a query."""
        try:
            results = []
            query_lower = query.lower()

            for entity_id, entity in self.knowledge_entities.items():
                # Filter by entity type if specified
                if entity_types and entity.entity_type.value not in entity_types:
                    continue

                score = 0.0

                # Name match
                if query_lower in entity.name.lower():
                    score += 0.5

                # Tag match
                for tag in entity.tags:
                    if query_lower in tag.lower():
                        score += 0.3

                # Property match
                for key, value in entity.properties.items():
                    if query_lower in str(value).lower():
                        score += 0.2

                if score > 0:
                    # Update access tracking
                    entity.access_count += 1
                    entity.last_accessed = datetime.now()

                    results.append(
                        {
                            "entity_id": entity_id,
                            "name": entity.name,
                            "type": entity.entity_type.value,
                            "score": score,
                            "importance": entity.importance_score,
                            "properties": entity.properties,
                            "tags": entity.tags,
                        }
                    )

            # Sort by score and importance
            results.sort(key=lambda x: (x["score"], x["importance"]), reverse=True)
            return results[:20]  # Return top 20 results

        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []

    def _load_organization_data(self):
        """Load organization data from storage."""
        try:
            data_file = "knowledge_organizer_data.json"
            if os.path.exists(data_file):
                with open(data_file, "r") as f:
                    data = json.load(f)

                # Load entities
                for entity_data in data.get("entities", []):
                    entity = KnowledgeEntity(
                        entity_id=entity_data["entity_id"],
                        entity_type=KnowledgeEntityType(entity_data["entity_type"]),
                        name=entity_data["name"],
                        properties=entity_data["properties"],
                        importance_score=entity_data["importance_score"],
                        creation_time=datetime.fromisoformat(entity_data["creation_time"]),
                        last_accessed=datetime.fromisoformat(entity_data["last_accessed"]),
                        access_count=entity_data.get("access_count", 0),
                        tags=entity_data.get("tags", []),
                    )
                    self.knowledge_entities[entity.entity_id] = entity

                # Load relationships
                for rel_data in data.get("relationships", []):
                    relationship = KnowledgeRelationship(
                        relationship_id=rel_data["relationship_id"],
                        source_entity_id=rel_data["source_entity_id"],
                        target_entity_id=rel_data["target_entity_id"],
                        relationship_type=RelationshipType(rel_data["relationship_type"]),
                        strength=rel_data["strength"],
                        confidence=rel_data["confidence"],
                        evidence=rel_data["evidence"],
                        created_at=datetime.fromisoformat(rel_data["created_at"]),
                        last_reinforced=datetime.fromisoformat(rel_data["last_reinforced"]),
                    )
                    self.knowledge_relationships[relationship.relationship_id] = relationship

                # Rebuild graph and indices
                self._rebuild_graph_and_indices()

                logger.info(f"Loaded {len(self.knowledge_entities)} entities and {len(self.knowledge_relationships)} relationships")

        except Exception as e:
            logger.warning(f"Could not load organization data: {e}")

    def _rebuild_graph_and_indices(self):
        """Rebuild the knowledge graph and indices."""
        try:
            # Clear existing structures
            self.knowledge_graph.clear()
            self.entity_type_index.clear()
            self.tag_index.clear()
            self.temporal_index.clear()

            # Rebuild graph
            for entity_id, entity in self.knowledge_entities.items():
                self.knowledge_graph.add_node(entity_id, **entity.properties)

                # Rebuild indices
                self.entity_type_index[entity.entity_type].add(entity_id)
                for tag in entity.tags:
                    self.tag_index[tag].add(entity_id)

                date_key = entity.creation_time.strftime("%Y-%m-%d")
                self.temporal_index[date_key].append(entity_id)

            # Add relationships to graph
            for relationship in self.knowledge_relationships.values():
                if relationship.source_entity_id in self.knowledge_entities and relationship.target_entity_id in self.knowledge_entities:
                    self.knowledge_graph.add_edge(
                        relationship.source_entity_id,
                        relationship.target_entity_id,
                        relationship_type=relationship.relationship_type.value,
                        strength=relationship.strength,
                        confidence=relationship.confidence,
                    )

            logger.debug("Rebuilt knowledge graph and indices")

        except Exception as e:
            logger.error(f"Error rebuilding graph and indices: {e}")

    def save_organization_data(self):
        """Save organization data to storage."""
        try:
            data = {"entities": [], "relationships": []}

            # Save entities
            for entity in self.knowledge_entities.values():
                entity_data = {
                    "entity_id": entity.entity_id,
                    "entity_type": entity.entity_type.value,
                    "name": entity.name,
                    "properties": entity.properties,
                    "importance_score": entity.importance_score,
                    "creation_time": entity.creation_time.isoformat(),
                    "last_accessed": entity.last_accessed.isoformat(),
                    "access_count": entity.access_count,
                    "tags": entity.tags,
                }
                data["entities"].append(entity_data)

            # Save relationships
            for relationship in self.knowledge_relationships.values():
                rel_data = {
                    "relationship_id": relationship.relationship_id,
                    "source_entity_id": relationship.source_entity_id,
                    "target_entity_id": relationship.target_entity_id,
                    "relationship_type": relationship.relationship_type.value,
                    "strength": relationship.strength,
                    "confidence": relationship.confidence,
                    "evidence": relationship.evidence,
                    "created_at": relationship.created_at.isoformat(),
                    "last_reinforced": relationship.last_reinforced.isoformat(),
                }
                data["relationships"].append(rel_data)

            with open("knowledge_organizer_data.json", "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Organization data saved successfully")

        except Exception as e:
            logger.error(f"Error saving organization data: {e}")

    def process(self, input_data: Any) -> ExecutionResult:
        """Process input through the knowledge organizer."""
        try:
            if isinstance(input_data, dict):
                command = input_data.get("command")

                if command == "add_entity":
                    entity_data = input_data.get("entity_data", {})
                    entity_id = self.add_knowledge_entity(entity_data)
                    return ExecutionResult(success=bool(entity_id), message="Entity added successfully" if entity_id else "Failed to add entity", data={"entity_id": entity_id})

                elif command == "add_relationship":
                    relationship_data = input_data.get("relationship_data", {})
                    relationship_id = self.add_relationship(relationship_data)
                    return ExecutionResult(
                        success=bool(relationship_id), message="Relationship added successfully" if relationship_id else "Failed to add relationship", data={"relationship_id": relationship_id}
                    )

                elif command == "get_graph_structure":
                    structure = self.get_knowledge_graph_structure()
                    return ExecutionResult(success=True, message="Knowledge graph structure retrieved", data=structure)

                elif command == "consolidate":
                    results = self.consolidate_knowledge()
                    return ExecutionResult(success=True, message="Knowledge consolidation completed", data=results)

                elif command == "search":
                    query = input_data.get("query", "")
                    entity_types = input_data.get("entity_types")
                    results = self.search_knowledge(query, entity_types)
                    return ExecutionResult(success=True, message=f"Found {len(results)} matching entities", data={"results": results})

                elif command == "discover_relationships":
                    entity_id = input_data.get("entity_id")
                    if entity_id:
                        relationships = self.discover_relationships(entity_id)
                        return ExecutionResult(success=True, message=f"Discovered {len(relationships)} potential relationships", data={"relationships": relationships})

            return ExecutionResult(success=False, message="Invalid input for AdvancedKnowledgeOrganizer", data={})

        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return ExecutionResult(success=False, message=f"Processing error: {str(e)}", data={})

    def cleanup(self):
        """Clean up resources and save data."""
        self.save_organization_data()
        logger.info("AdvancedKnowledgeOrganizer cleanup completed")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass
