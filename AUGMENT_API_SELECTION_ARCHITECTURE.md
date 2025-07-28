# Augment Agent API Selection Architecture

## Overview

This document outlines the comprehensive architecture for enabling the Augment Agent to accurately and efficiently select the correct APIs from the Man-O-Man service registry. The system supports two modes: **Speed-Optimized** and **Maximum Accuracy**, allowing dynamic trade-offs between processing time and selection accuracy.

## Core Design Philosophy

### Service Registry Foundation
- **Single Source of Truth**: Comprehensive service registry enhanced by Proxie Agent
- **Augment-Optimized Metadata**: All enhancements specifically designed to improve Augment's API selection capabilities
- **Continuous Learning**: Registry continuously improved based on real usage patterns and success rates

### Two-Stage Selection Process
1. **Service Identification**: Determine which service(s) contain relevant APIs
2. **API Selection**: Choose the optimal API within the identified service(s)

### Hybrid Classification Approach
- **Offline Pre-processing**: Heavy computation moved to Proxie's enhancement phase
- **Runtime Optimization**: Fast traditional ML/IR techniques for real-time selection
- **LLM Integration**: Strategic use of lightweight LLMs for final decision-making

## Architecture Mode 1: Speed-Optimized (Target: <300ms, >85% accuracy)

### Core Pipeline
```
User Query → Intent Feature Extraction → Multi-Model Service Classification → API Classification → Light LLM Decision
```

### Stage 1: Intent Feature Extraction (<10ms)
```python
def extract_intent_features(user_query):
    return {
        'action_verbs': extract_verbs(query),  # create, add, delete, etc.
        'entity_nouns': extract_entities(query),  # user, ticket, asset, etc.
        'intent_keywords': extract_keywords(query),
        'tfidf_vector': tfidf_vectorizer.transform([query]),
        'semantic_embedding': sentence_transformer.encode(query),
        'query_length': len(query.split()),
        'question_type': classify_question_type(query),  # create, read, update, delete, search
        'complexity_indicators': detect_complexity_markers(query)
    }
```

### Stage 2: Multi-Model Service Classification (<50ms)
```python
def classify_services(intent_features):
    # Parallel classification using multiple methods
    
    # 1. TF-IDF Similarity (Fastest)
    tfidf_scores = cosine_similarity(
        intent_features['tfidf_vector'], 
        service_tfidf_matrix
    )
    
    # 2. Semantic Search (Fast)
    semantic_scores = faiss_index.search(
        intent_features['semantic_embedding'],
        k=10
    )
    
    # 3. Keyword Matching (Fastest)
    keyword_scores = fuzzy_keyword_match(
        intent_features['intent_keywords'],
        service_keyword_db
    )
    
    # 4. Traditional ML Classifier (Fast)
    ml_scores = trained_service_classifier.predict_proba(
        intent_features['feature_vector']
    )
    
    # 5. Rule-Based Classification (Fastest)
    rule_scores = rule_engine.classify(intent_features)
    
    # Ensemble scoring with learned weights
    final_scores = ensemble_combine([
        (tfidf_scores, 0.25),
        (semantic_scores, 0.30),
        (keyword_scores, 0.20), 
        (ml_scores, 0.15),
        (rule_scores, 0.10)
    ])
    
    return get_top_k_services(final_scores, k=3)
```

### Stage 3: API Classification within Services (<100ms)
```python
def classify_apis_for_services(intent_features, top_services):
    candidate_apis = []
    
    for service in top_services:
        service_apis = api_registry.get_apis(service.id)
        
        # Tier-based filtering first (fastest)
        if intent_features['complexity'] == 'simple':
            filtered_apis = [api for api in service_apis if api.tier == 1]
        else:
            filtered_apis = service_apis
            
        # API-specific classification
        for api in filtered_apis:
            score = calculate_api_score(intent_features, api)
            if score > confidence_threshold:
                candidate_apis.append((api, score, service.confidence))
    
    return rank_apis(candidate_apis)

def calculate_api_score(intent_features, api):
    # Fast scoring based on pre-computed features
    action_match = action_verb_match(intent_features['action_verbs'], api.action_patterns)
    entity_match = entity_noun_match(intent_features['entity_nouns'], api.entity_patterns)
    param_complexity_match = complexity_match(intent_features, api.complexity)
    
    # Weighted combination
    return (action_match * 0.4 + entity_match * 0.4 + param_complexity_match * 0.2)
```

### Stage 4: Light LLM Final Selection (<200ms)
```python
def light_llm_selection(user_query, top_3_apis):
    # Minimal prompt with pre-classified options
    prompt = f"""
User: {user_query}
Pre-classified API options:
1. {api1.method} {api1.endpoint} - {api1.one_line_desc} (confidence: {api1.score:.2f})
2. {api2.method} {api2.endpoint} - {api2.one_line_desc} (confidence: {api2.score:.2f})
3. {api3.method} {api3.endpoint} - {api3.one_line_desc} (confidence: {api3.score:.2f})

Best choice: """

    # Use Gemma 3B for final selection only
    response = gemma_3b.generate(prompt, max_tokens=50)
    return parse_selection(response)
```

## Architecture Mode 2: Maximum Accuracy (Target: ~1000ms, >98% accuracy)

### Enhanced Pipeline
```
User Query → Enhanced Feature Extraction → Multi-Model Pre-filtering → Cross-Encoder Verification → Deep API Matching → Enhanced LLM Reasoning → Validation & Fallback
```

### Stage 1: Enhanced Feature Extraction (50ms)
```python
def enhanced_feature_extraction(user_query):
    features = {
        'query_embedding': sentence_transformer.encode(query),
        'action_verbs': extract_action_verbs(query),
        'entity_nouns': extract_entities_with_context(query),
        'intent_modifiers': extract_modifiers(query),  # urgent, bulk, simple, etc.
        'question_type': classify_question_type(query),
        'tense_analysis': extract_tense(query),  # past, present, future
        'negation_patterns': detect_negations(query),
        'conditional_patterns': detect_conditionals(query),
        'workflow_indicators': detect_workflow_context(query),
        'business_context': extract_business_context(query)
    }
    return features
```

### Stage 2: Cross-Encoder Deep Verification (200ms)
```python
def cross_encoder_verification(query, candidate_services):
    verification_scores = []
    
    for service in candidate_services:
        # Create rich context for cross-encoder
        context = f"""
        Query: {query}
        Service: {service.name}
        Description: {service.enhanced_description}
        Typical Use Cases: {service.use_cases}
        Keywords: {service.intent_keywords}
        Example Queries: {service.example_queries}
        """
        
        # Use trained cross-encoder for deep semantic matching
        relevance_score = cross_encoder_model.predict(context)
        
        # Additional verification layers
        keyword_overlap = calculate_keyword_overlap(query, service)
        semantic_similarity = calculate_deep_semantic_similarity(query, service)
        context_appropriateness = assess_context_match(query, service)
        
        final_score = combine_scores([
            (relevance_score, 0.4),
            (keyword_overlap, 0.2), 
            (semantic_similarity, 0.3),
            (context_appropriateness, 0.1)
        ])
        
        verification_scores.append((service, final_score))
    
    return rank_and_filter_by_confidence(verification_scores, min_confidence=0.7)
```

### Stage 3: Deep API Matching with Parameter Analysis (300ms)
```python
def deep_api_matching(query, verified_services, intent_features):
    candidate_apis = []
    
    for service in verified_services:
        service_apis = get_enhanced_apis(service.id)
        
        for api in service_apis:
            # Multi-dimensional API scoring
            scores = {
                'intent_match': calculate_intent_api_match(intent_features, api),
                'parameter_feasibility': assess_parameter_feasibility(query, api),
                'success_probability': api.historical_success_rate,
                'complexity_match': assess_complexity_alignment(query, api),
                'response_appropriateness': evaluate_response_match(query, api),
                'workflow_position': assess_workflow_fit(query, api)
            }
            
            # Contextual parameter analysis
            param_analysis = analyze_parameter_requirements(query, api)
            
            # Deep semantic API-query matching
            api_context = f"""
            User Intent: {query}
            API: {api.method} {api.endpoint}
            Purpose: {api.enhanced_description}
            Parameters: {api.parameter_descriptions}
            Response: {api.response_description}
            When to Use: {api.usage_context}
            """
            
            semantic_match = api_cross_encoder.predict(api_context)
            
            final_api_score = weighted_combination(scores, semantic_match)
            
            if final_api_score > confidence_threshold:
                candidate_apis.append({
                    'api': api,
                    'score': final_api_score,
                    'param_analysis': param_analysis,
                    'confidence_breakdown': scores
                })
    
    return rank_apis_with_explanations(candidate_apis)
```

### Stage 4: Enhanced LLM Reasoning Chain (400ms)
```python
def enhanced_llm_decision(query, top_apis):
    # Create rich context for LLM reasoning
    context = f"""
    USER QUERY: {query}
    
    ANALYSIS CONTEXT:
    - Intent Type: {intent_analysis.type}
    - Complexity Level: {intent_analysis.complexity}
    - Entity Focus: {intent_analysis.entities}
    - Action Required: {intent_analysis.actions}
    
    TOP API CANDIDATES:
    """
    
    for i, api_candidate in enumerate(top_apis, 1):
        context += f"""
        
        OPTION {i}: {api_candidate.api.method} {api_candidate.api.endpoint}
        - Purpose: {api_candidate.api.enhanced_description}
        - Match Score: {api_candidate.score:.3f}
        - Why Suggested: {api_candidate.reasoning}
        - Parameter Requirements: {api_candidate.param_analysis.summary}
        - Success Probability: {api_candidate.api.success_rate:.2%}
        - Typical Use: {api_candidate.api.usage_context}
        - Potential Issues: {api_candidate.api.known_issues}
        """
    
    # Enhanced reasoning prompt
    prompt = f"""
    {context}
    
    REASONING REQUIREMENTS:
    1. Analyze the user's specific intent and requirements
    2. Consider parameter complexity and availability  
    3. Evaluate success probability and potential issues
    4. Assess if this is a simple request or part of a larger workflow
    5. Consider alternative approaches if confidence is low
    
    DECISION FORMAT:
    Selected API: [Number and endpoint]
    Confidence: [0.0-1.0]
    Reasoning: [Detailed explanation]
    Parameter Strategy: [How to handle parameters]
    Fallback Options: [Alternative approaches if this fails]
    
    DECISION:
    """
    
    response = enhanced_llm.generate(prompt, max_tokens=300, temperature=0.1)
    return parse_enhanced_decision(response)
```

### Stage 5: Validation & Fallback System (100ms)
```python
def validation_and_fallback(llm_decision, original_query):
    # Multi-layer validation
    validations = {
        'confidence_check': llm_decision.confidence > 0.8,
        'parameter_feasibility': validate_parameter_feasibility(llm_decision),
        'historical_success': check_historical_success_rate(llm_decision.api),
        'context_consistency': validate_context_consistency(original_query, llm_decision),
        'logical_coherence': validate_logical_coherence(llm_decision.reasoning)
    }
    
    validation_score = sum(validations.values()) / len(validations)
    
    if validation_score < 0.8:
        # Implement fallback strategies
        fallback_options = {
            'alternative_apis': find_alternative_apis(original_query),
            'simplified_approach': find_simpler_alternatives(original_query),
            'human_escalation': prepare_human_escalation(original_query, llm_decision),
            'clarification_questions': generate_clarification_questions(original_query)
        }
        
        return select_best_fallback(fallback_options, validation_score)
    
    return llm_decision
```

## Proxie-Enhanced Service Registry Schema

### Service-Level Metadata for Augment
```json
{
  "service_name": "user_management",
  "augment_optimization": {
    "intent_keywords": ["create", "user", "account", "register", "add", "employee"],
    "semantic_category": "user_management.creation",
    "business_actions": ["CREATE_USER_ACCOUNT", "REGISTER_EMPLOYEE"],
    "user_intent_patterns": [
      "I want to create a user",
      "Add a new user account", 
      "Register someone in the system",
      "Create an employee account"
    ],
    "negative_examples": [
      "delete ticket", "create incident", "update asset"
    ],
    "execution_context": {
      "complexity_level": "simple",
      "when_to_use": "For basic user creation with minimal required fields",
      "when_not_to_use": "When bulk user creation or complex role assignment needed",
      "prerequisites": ["admin_authentication_required"],
      "side_effects": ["triggers_welcome_email", "creates_default_permissions"]
    },
    "confidence_indicators": {
      "strong_indicators": ["create", "new", "add"] + ["user", "account", "employee"],
      "weak_indicators": ["manage", "handle", "process"],
      "anti_indicators": ["delete", "remove", "update", "modify"]
    }
  }
}
```

### API-Level Metadata for Augment
```json
{
  "api_endpoint": "/users",
  "method": "POST",
  "tier": 1,
  "augment_optimization": {
    "intent_specificity": 0.95,
    "parameter_complexity": "low",
    "success_patterns": ["create", "new", "add"] + ["user", "account"],
    "failure_patterns": ["update", "modify", "change"],
    "discriminative_features": ["requires_email", "auto_generates_id"],
    "parameter_guidance": {
      "username": {
        "llm_generation_hint": "Generate realistic username (firstname.lastname format preferred)",
        "validation_pattern": "^[a-zA-Z0-9._]+$",
        "common_failures": ["spaces_not_allowed", "must_be_unique"],
        "auto_generate": true,
        "examples": ["john.doe", "sarah.smith", "mike.johnson"]
      },
      "email": {
        "llm_generation_hint": "Use domain @company.com for internal users",
        "required_for_success": true,
        "validation_example": "john.doe@infraon.com"
      }
    },
    "workflow_role": "step_1_of_3",
    "typical_sequences": [
      {
        "workflow_name": "complete_user_onboarding",
        "sequence": [
          {"step": 1, "api": "create_user", "required_output": "user_id"},
          {"step": 2, "api": "assign_role", "input_from_previous": "user_id"},
          {"step": 3, "api": "send_welcome_email", "input_from_previous": "user_id"}
        ]
      }
    ],
    "error_recovery": {
      "common_errors": [
        {
          "error_pattern": "username_already_exists",
          "recovery_action": "append_random_number_and_retry",
          "alternative_apis": ["create_user_with_auto_username"]
        },
        {
          "error_pattern": "insufficient_permissions",
          "recovery_action": "escalate_to_admin_user_creation_api",
          "alternative_apis": ["request_user_creation_approval"]
        }
      ],
      "fallback_strategies": ["use_simplified_creation", "defer_to_manual_process"]
    }
  }
}
```

## Performance Optimization Strategies

### Database Schema for Ultra-Fast Retrieval
```sql
-- Service Classification Cache
CREATE TABLE service_intent_cache (
    intent_hash VARCHAR(64) PRIMARY KEY,
    service_rankings JSONB, -- Pre-computed service scores
    confidence_score FLOAT,
    last_updated TIMESTAMP,
    INDEX(intent_hash)
);

-- API Classification Cache  
CREATE TABLE api_intent_cache (
    intent_service_hash VARCHAR(64) PRIMARY KEY,
    api_rankings JSONB, -- Pre-computed API scores for service
    confidence_score FLOAT,
    last_updated TIMESTAMP,
    INDEX(intent_service_hash)
);

-- Fast lookup indexes
CREATE INDEX idx_service_keywords ON services USING GIN(intent_keywords);
CREATE INDEX idx_api_patterns ON apis USING GIN(action_patterns, entity_patterns);
CREATE INDEX idx_augment_metadata ON apis USING GIN(augment_optimization);
```

### Caching Strategy
```python
# Redis caching for common queries
CACHE_CONFIG = {
    'intent_hash_ttl': 3600,  # 1 hour
    'service_rankings_ttl': 1800,  # 30 minutes
    'api_scores_ttl': 900,  # 15 minutes
    'fallback_options_ttl': 600  # 10 minutes
}

def get_cached_classification(intent_hash):
    cached_result = redis_client.get(f"classification:{intent_hash}")
    if cached_result:
        return json.loads(cached_result)
    return None

def cache_classification(intent_hash, result):
    redis_client.setex(
        f"classification:{intent_hash}",
        CACHE_CONFIG['intent_hash_ttl'],
        json.dumps(result)
    )
```

## Training Strategy for Maximum Accuracy

### 1. Service Classification Training
```python
def generate_service_training_data():
    training_data = []
    
    for service in enhanced_services:
        # Positive examples
        for intent_pattern in service.intent_patterns:
            training_data.append({
                'text': intent_pattern,
                'label': service.id,
                'features': extract_features(intent_pattern),
                'type': 'positive'
            })
        
        # Negative examples (crucial for accuracy)
        for negative_example in service.negative_examples:
            training_data.append({
                'text': negative_example,
                'label': f"NOT_{service.id}",
                'features': extract_features(negative_example),
                'type': 'negative'
            })
    
    return training_data

# Train ensemble of specialized classifiers
def train_classification_ensemble():
    models = {
        'svm_linear': SVM(kernel='linear', class_weight='balanced'),
        'random_forest': RandomForestClassifier(n_estimators=200, class_weight='balanced'),
        'xgboost': XGBClassifier(scale_pos_weight=calculate_scale_pos_weight()),
        'naive_bayes': MultinomialNB(alpha=0.1),
        'logistic_regression': LogisticRegression(class_weight='balanced', max_iter=1000)
    }
    
    for name, model in models.items():
        model.fit(training_features, training_labels)
        validate_model_performance(model, validation_set)
```

### 2. Active Learning Pipeline
```python
def active_learning_update():
    # Get uncertain predictions from production
    uncertain_queries = get_low_confidence_queries(confidence_threshold=0.8)
    
    # Get user feedback on these queries
    for query in uncertain_queries:
        true_service = get_user_feedback(query)
        true_api = get_api_feedback(query, true_service)
        
        # Add to training data
        add_to_training_set(query, true_service, true_api)
        
        # Retrain models incrementally
        incremental_model_update(query, true_service, true_api)

def continuous_improvement_loop():
    # Track Augment's success rates
    success_metrics = track_augment_performance()
    
    # Identify failure patterns
    failure_patterns = analyze_failure_modes(success_metrics)
    
    # Update training data based on failures
    augment_training_data_with_failures(failure_patterns)
    
    # Retrain models
    retrain_models_with_augmented_data()
```

## Mode Selection Strategy

### Dynamic Mode Selection
```python
def select_accuracy_mode(query, context):
    factors = {
        'query_complexity': assess_query_complexity(query),
        'task_criticality': determine_task_criticality(context),
        'user_preference': get_user_accuracy_preference(),
        'system_load': check_current_system_load(),
        'available_time': calculate_available_processing_time(),
        'confidence_history': get_user_confidence_history()
    }
    
    if factors['task_criticality'] == 'high' or factors['query_complexity'] == 'complex':
        return 'maximum_accuracy'
    elif factors['user_preference'] == 'speed' and factors['system_load'] == 'high':
        return 'speed_optimized'
    else:
        return 'balanced'  # Default mode
```

### Configuration Options
```python
ACCURACY_MODES = {
    'speed_optimized': {
        'max_time_ms': 300,
        'target_accuracy': 85,
        'stages': ['feature_extraction', 'multi_model_classification', 'light_llm'],
        'models': ['tfidf', 'keyword_match', 'simple_ml', 'gemma_3b'],
        'confidence_threshold': 0.7
    },
    'balanced': {
        'max_time_ms': 600, 
        'target_accuracy': 92,
        'stages': ['enhanced_features', 'cross_encoder', 'api_matching', 'llm_decision'],
        'models': ['full_ensemble', 'cross_encoder', 'gemma_3b'],
        'confidence_threshold': 0.8
    },
    'maximum_accuracy': {
        'max_time_ms': 1000,
        'target_accuracy': 98,
        'stages': ['full_pipeline'],
        'models': ['full_ensemble', 'cross_encoder', 'enhanced_llm', 'validation'],
        'confidence_threshold': 0.9,
        'fallback_enabled': True,
        'multi_llm_verification': True
    }
}
```

## Integration with Augment Agent

### Augment Agent API Selection Interface
```python
class AugmentAPISelector:
    def __init__(self, mode='balanced'):
        self.mode = mode
        self.pipeline = initialize_pipeline(mode)
        
    async def select_api(self, user_query, context=None):
        # Select processing mode
        processing_mode = self.select_mode(user_query, context)
        
        # Execute appropriate pipeline
        if processing_mode == 'speed_optimized':
            result = await self.speed_optimized_pipeline(user_query)
        elif processing_mode == 'maximum_accuracy':
            result = await self.maximum_accuracy_pipeline(user_query)
        else:
            result = await self.balanced_pipeline(user_query)
        
        # Track performance for continuous improvement
        self.track_selection_performance(user_query, result)
        
        return result
    
    async def get_parameter_guidance(self, selected_api, user_query):
        # Get Proxie-enhanced parameter guidance
        guidance = await self.parameter_guidance_engine.generate_guidance(
            api=selected_api,
            user_intent=user_query,
            context=self.context
        )
        return guidance
```

## Success Metrics and Monitoring

### Key Performance Indicators
```python
MONITORING_METRICS = {
    'accuracy_metrics': {
        'service_classification_accuracy': '>95%',
        'api_selection_accuracy': '>90%',
        'end_to_end_success_rate': '>85%',
        'confidence_calibration_error': '<5%'
    },
    'performance_metrics': {
        'average_response_time': {
            'speed_mode': '<300ms',
            'balanced_mode': '<600ms', 
            'accuracy_mode': '<1000ms'
        },
        'cache_hit_rate': '>80%',
        'system_throughput': '>100 requests/second'
    },
    'user_satisfaction_metrics': {
        'task_completion_rate': '>90%',
        'user_confidence_in_results': '>85%',
        'error_recovery_success_rate': '>80%'
    }
}
```

### Continuous Monitoring Dashboard
```python
def create_monitoring_dashboard():
    metrics = {
        'real_time_accuracy': track_real_time_accuracy(),
        'performance_trends': analyze_performance_trends(),
        'failure_analysis': analyze_failure_patterns(),
        'user_feedback': aggregate_user_feedback(),
        'model_drift_detection': detect_model_drift(),
        'system_health': monitor_system_health()
    }
    return metrics
```

## Future Enhancements

### Advanced AI Capabilities
- **Multi-Modal Input Processing**: Support for voice queries and images
- **Context-Aware Learning**: Learn from user interaction patterns
- **Predictive API Selection**: Anticipate user needs based on workflow patterns
- **Natural Language API Documentation**: Generate human-readable API guides

### Enterprise Features
- **Multi-Tenant Support**: Isolated registries for different organizations
- **Role-Based API Access**: Ensure users only see APIs they can access
- **Compliance Checking**: Ensure selected APIs meet security requirements
- **Performance Analytics**: Track API usage patterns and optimization opportunities

---

**Note**: This architecture represents a comprehensive approach to API selection that balances speed, accuracy, and user experience. The system is designed to learn and improve continuously, becoming more accurate and efficient over time through the integration of user feedback and real-world usage patterns.