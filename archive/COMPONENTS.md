# SYSTEM COMPONENTS

## 3.1 USER INTERFACE

Responsibility:
The user interface accepts open-ended natural language queries.

Example queries:
"I want a gaming laptop under $1500"
"Build a home office setup"
"I need a lightweight laptop for coding and travel"

Technology options:
Streamlit (simple interface)
FastAPI with frontend

## 3.2 INTENT AGENT

Responsibility:
Convert natural language input into a structured representation of user intent.

Example structured intent:

{
category: laptop
purpose: gaming
budget: 1500
preferences: lightweight
uncertainty: battery life
}

Agentic AI Events emitted:
INTENT_PARSED
INTENT_UNCERTAIN

INTENT_UNCERTAIN is triggered when required information is missing.

## 3.3 CLARIFICATION AGENT

Responsibility:
Resolve ambiguity in the user's intent.

If the intent contains missing attributes such as budget or preferred category, the system asks clarification questions.

Example:
User query: "I want a gaming laptop"

System response:
"What is your budget?"

Agentic AI Events:
CLARIFICATION_REQUESTED
INTENT_REFINED

INTENT_REFINED represents an updated structured intent.

## 3.4 RETRIEVAL AGENT

Responsibility:
Retrieve candidate products from the product catalog.

The agent dynamically selects a retrieval strategy depending on the clarity of the intent.

Possible retrieval strategies:
Semantic Search
Filter Search
Hybrid Search

Agentic AI Events:
RETRIEVAL_STRATEGY_SELECTED
CONTEXT_ACCEPTED
CONTEXT_REJECTED

CONTEXT_ACCEPTED indicates relevant products were retrieved.
CONTEXT_REJECTED indicates irrelevant products were filtered out.

## 3.5 REASONING AGENT

Responsibility:
Compare candidate products and determine which ones best satisfy the user's intent.

The reasoning agent evaluates trade-offs between alternatives.

Example reasoning:

Laptop A:
Good GPU
Cheaper
Weak battery

Laptop B:
Stronger GPU
Exceeds budget

Agentic AI Events:
REASONING_PATH_CHOSEN
GOAL_CONFLICT_DETECTED

Example conflict:
Performance vs Budget

## 3.6 CART AGENT

Responsibility:
Construct and update the shopping cart.

Possible actions:
Add item
Remove item
Replace item

Example cart:
Laptop
Mouse
Monitor
Keyboard

Agentic AI Events:
CART_UPDATED
CART_STABLE

CART_STABLE indicates that no further cart modifications are required.

## 3.7 EVALUATION AGENT (ONLINE EVALUATION)

Responsibility:
Evaluate the quality of the current cart and determine whether the system should continue planning or terminate.

Example checks:
Cart exceeds budget
Items incompatible
Cart incomplete

Possible outcomes:
Trigger a new planning loop
Terminate the task

Agentic AI Events:
GOAL_CONFLICT_DETECTED
LOOP_TRIGGERED
TASK_TERMINATED

## 3.8 LOOP CONTROLLER

Responsibility:
Control agentic loops in the system.

It determines whether to:
Refine intent
Re-run retrieval
Re-plan the cart
Terminate execution