# 1 Use-Case Name
Chat with AIBot

## 1.1 Brief Description
Authenticated users can interact with an AI research assistant to ask questions and receive general, evidence-based suggestions about market data and financial news. The assistant relies on documented analysis, states its assumptions, and explicitly refuses to provide personalized investment advice.

# 2 Flow of Events
## 2.1 Basic Flow
- User opens the AI chat interface and types a question regarding a specific stock or market condition.
- UI sends the user's query to the system.
- System retrieves available market data, news, risk indicators, and documented analysis relevant to the query.
- System queries the AI service to generate a response using only the retrieved data.
- System returns the AI response, including citations and identified assumptions.
- UI displays the response and explicitly notes the limitations of the provided data.

### 2.1.1 Activity Diagram
![Chat with AIBot Activity Diagram](../Media/ChatWithAIBotActivityDiagramm.jpg)

### 2.1.2 Mock-up
Design source: [Figma](https://www.figma.com/design/bBspMfnXbO5TzTM1VUkKjH)

**C1: Chat interface (empty or active)**
![Chat interface](</documentation/Media/C1 - Chat interface.png>)

**C2: Bot typing/loading state**
![Bot typing](</documentation/Media/C2 - Bot loading state.png>)

**C3: Bot response with sources and assumptions**
![Bot response](</documentation/Media/C3 - Bot response.png>)

**C4: Bot refusal (personalized advice requested)**
![Bot refusal](</documentation/Media/C4 - Bot refusal.png>)

**CRUD:** Chat with AIBot is a Create and Read use case.
- Create: send message to bot (C1, C2)
- Read: view bot responses, sources, and limitations (C1, C3, C4)
- ~~Update~~: struck out, messages cannot be edited.
- ~~Delete~~: struck out, clearing chat history is not explicitly defined in scope.

### 2.1.3 Narrative
```gherkin
Feature: chat with AI bot

  As a signed in user
  I want to ask an AI assistant about stocks
  in order to receive general suggestions and understand available market data.

  Background:
    And I am on the homepage

  Scenario: ask a supported question
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the "AI chat" page
    When I send the message "What is the recent sentiment for AAPL?"
    Then I see a loading indicator
    And the bot replies with an evidence-based summary of AAPL's recent news sentiment
    And the response clearly identifies the sources and assumptions

  Scenario: ask for investment advice
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the "AI chat" page
    When I send the message "Should I buy AAPL right now?"
    Then the bot replies with a statement that it cannot provide personalized investment advice
    And the bot offers general market data instead
```

## 2.2 Alternative Flows
### 2.2.1 Information Unavailable
- User asks a question about an obscure stock or a topic where data is unavailable.
- System determines that evidence is insufficient to support a conclusion.
- UI displays a response from the bot clearly stating that the requested information is unavailable.

# 3 Special Requirements
## 3.1 No Personalized Advice
The AI must not instruct a user to buy, sell, or hold a specific instrument, nor can it provide personalized investment advice. It must avoid hunch-based or unsupported speculative claims and use neutral language.

## 3.2 Untrusted Input Handling
Text processed by the AI (e.g., from external news sources) must be treated as untrusted, properly encoded, and never executed as automated instructions.

# 4 Preconditions
## 4.1 Login
The user has to be logged in to the system.

# 5 Postconditions
## 5.1 Response Delivered
The user receives a compliant, evidence-based response or a polite refusal if the query violates compliance rules.

# 6 Extension Points
## 6.1 Generate Structured Research Brief
The user can request the bot to formulate its response into a full structured research brief, initiating the "Generate structured research brief" use case.