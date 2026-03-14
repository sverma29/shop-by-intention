# AGENTIC LOOPS

The system contains multiple loops where the agent reevaluates its decisions.

## Loop 1: Intent Refinement Loop

INTENT_PARSED
-> INTENT_UNCERTAIN
-> CLARIFICATION_REQUESTED
-> INTENT_REFINED

The loop continues until the intent becomes sufficiently clear.

## Loop 2: Retrieval-Reasoning Loop

Retrieve products
-> Evaluate products
-> GOAL_CONFLICT_DETECTED
-> Adjust retrieval strategy
-> Retrieve again

## Loop 3: Cart Optimization Loop

Cart constructed
-> Evaluate cart
-> Detect improvement opportunity
-> Replan cart

## AGENTIC AI EVENT MODEL

Event taxonomy used in the system:

INTENT_PARSED
INTENT_UNCERTAIN
CLARIFICATION_REQUESTED
INTENT_REFINED
RETRIEVAL_STRATEGY_SELECTED
CONTEXT_ACCEPTED
CONTEXT_REJECTED
REASONING_PATH_CHOSEN
GOAL_CONFLICT_DETECTED
CART_UPDATED
LOOP_TRIGGERED
TASK_TERMINATED

## EVENT SCHEMA

Each Agentic AI Event is logged in structured format.

Example event structure:

{
event_id: uuid
timestamp: ISO time
event_type: INTENT_PARSED
agent: IntentAgent
input_state: {}
decision: {}
output_state: {}
confidence: 0.82
}

Events are stored as JSON logs.