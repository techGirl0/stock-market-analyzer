# 1 Use-Case Name
Generate Research Brief

## 1.1 Brief Description
Users can utilize the platform's AI research assistant to generate a structured, evidence-based research brief for a selected stock. The brief provides a comprehensive overview, including a market snapshot, news sentiment summary, risk indicators, and forecast scenarios. The system strictly relies on documented calculations and explicitly states its sources, ensuring no personalized investment advice is given.

# 2 Flow of Events
## 2.1 Basic Flow
- User clicks the "Generate Brief" button on a selected stock's dashboard.
- UI displays visible loading feedback to indicate the brief is being generated.
- System orchestrates the research agent to gather data (current quotes, historical patterns, news sentiment, risk scores, and scenario forecasts).
- System generates a structured brief citing the retrieved tool results and source IDs.
- UI displays the completed research brief, explicitly showing the sources and timestamps used to produce it.

### 2.1.1 Activity Diagram
![Generate Brief Activity Diagram](/documentation/Media/GenerateBriefActivityDiagramm.jpg)

### 2.1.2 Mock-up
![Generate Brief Mockup](/documentation/Pictures/Wireframes/GenerateBrief.png)

### 2.1.3 Narrative
### 2.1.3 Narrative
```gherkin
Feature: generate research brief

  As a user
  I want to generate a structured research brief for a specific stock
  In order to view a consolidated summary of its market snapshot, risk, and forecasts.

  Background:
    Given I am on the homepage

  Scenario: successfully generate research brief (Happy Path)
    Given I am on the "stock dashboard" page for "NVDA"
    When I press the "Generate Brief" button
    Then I should see a loading indicator
    And the system compiles data and generates the brief
    And I should see the "structured research brief" section
    And I should see data sources and timestamps attached to the analysis
    And the brief includes a disclaimer regarding investment advice

  Scenario: incomplete data for brief (Unhappy Path)
    Given I am on the "stock dashboard" page for "NVDA"
    And historical forecast data is partially unavailable
    When I press the "Generate Brief" button
    Then I should see the "structured research brief" section
    And I should see a clear note stating which data was unavailable

  Scenario: refuse personalized investment advice (Unhappy Path)
    Given I am on the "stock dashboard" page for "NVDA"
    When I submit a prompt asking "Should I buy NVDA right now?"
    Then the system refuses to provide a personalized buy or sell recommendation
    And the system displays the compliance disclaimer
```

## 2.2 Alternative Flows
### 2.2.1 Data Unavailable or Incomplete
- System attempts to gather data but finds a specific component (e.g., historical risk metrics) is missing or unavailable.
- System generates the brief with the available data.
- UI displays the brief but includes a clear, honest note indicating that the specific information was unavailable, rather than inventing facts or presenting incomplete analysis as confirmed.

### 2.2.2 Advice-Seeking Interaction
- User attempts to ask the research assistant for a personalized buy/sell recommendation via a follow-up prompt.
- System detects the advice-seeking intent using the intent classifier.
- System refuses to provide the recommendation and instead explains what it can provide (risk profile, scenarios) while displaying the required disclaimers.

# 3 Special Requirements
## 3.1 Compliance and Language Constraints
The generated brief must not present forecasts as guarantees, personalized advice, or a single mandatory price target. The system must use neutral language (e.g., "scenarios", "risk profile") and display a short note clarifying that results are uncertain and do not constitute investment advice. All figures must come from the system's documented calculations, never from the LLM's internal memory.

## 3.2 Traceability
Every factual sentence, number, or date in the research brief must cite its source or tool result.

# 4 Preconditions
## 4.1 Platform Access
The user must have the platform application open and be viewing a specific stock's dashboard. 

# 5 Postconditions
## 5.1 Brief Rendered
The system successfully displays the structured research brief with all necessary citations, disclaimers, and timestamps.
 
# 6 Extension Points
## 6.1 Chat with Follow-up Agent
After the brief is generated, the user can use the chat interface to ask follow-up questions about the stock. The assistant will answer using the available application data and documented analysis, maintaining the conversation's context.
