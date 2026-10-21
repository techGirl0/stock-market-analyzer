
# Stock Market Analyzer — Software Requirements Specification

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 Purpose](#11-purpose)
  - [1.2 Scope](#12-scope)
  - [1.3 Definitions, Acronyms and Abbreviations](#13-definitions-acronyms-and-abbreviations)
  - [1.4 References](#14-references)
  - [1.5 Overview](#15-overview)
- [2. Overall Description](#2-overall-description)
  - [2.1 Vision](#21-vision)
  - [2.2 Use Case Diagram](#22-use-case-diagram)
  - [2.3 Technology Stack](#23-technology-stack)
- [3. Specific Requirements](#3-specific-requirements)
  - [3.1 Functionality](#31-functionality)
  - [3.2 Usability](#32-usability)
  - [3.3 Reliability](#33-reliability)
  - [3.4 Performance](#34-performance)
  - [3.5 Supportability](#35-supportability)
  - [3.6 Design Constraints](#36-design-constraints)
  - [3.7 Online User Documentation and Help System Requirements](#37-online-user-documentation-and-help-system-requirements)
  - [3.8 Purchased Components](#purchased-components)
  - [3.9 Interfaces](#39-interfaces)
  - [3.10 Licensing Requirements](#310-licensing-requirements)
  - [3.11 Legal, Copyright and Other Notices](#311-legal-copyright-and-other-notices)
  - [3.12 Applicable Standards](#312-applicable-standards)
- [4. Supporting Information](#4-supporting-information)



## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements of the stock market analysis application.

The document specifies the intended system functionality, constraints, and expected behavior. It establishes a common basis for system design, implementation, testing, and evaluation and supports verification that the implemented system meets the defined requirements.

The intended audience includes developers, project stakeholders, course instructors, and reviewers involved in the development and evaluation of the application.


### 1.2 Scope

The stock market analysis application is designed to support the analysis and exploration of financial market information. It aims to provide users with relevant market data, financial news, and analytical insights through a centralized platform.

The planned system functionality includes:

- Searching for stocks using ticker symbols.
- Displaying current and historical stock market data.
- Presenting financial news related to selected stocks or companies.
- Analyzing financial news sentiment using natural language processing.
- Presenting risk indicators and relevant market insights.
- Providing forecasts or potential market scenarios while communicating uncertainty.

The system focuses on presenting and analyzing financial information. It is not intended to execute financial transactions or provide personalized investment recommendations. Analytical results and forecasts may contain uncertainty and do not guarantee future market performance.

The final scope and availability of individual features depend on the requirements agreed upon by the project team and the implementation constraints of the project.



### 1.3 Definitions, Acronyms and Abbreviations

| Term | Definition |
|---|---|
| SRS | Software Requirements Specification; a document that specifies the functional and non-functional requirements of a software system. |
| API | Application Programming Interface; an interface that enables communication between software components or external services. |
| AI | Artificial Intelligence; techniques used to perform tasks that typically require human intelligence. |
| NLP | Natural Language Processing; techniques used to process and analyze human language. |
| Stock Ticker | A symbol used to identify a publicly traded stock or other financial instrument. |
| Market Data | Financial data relating to market activity, including stock prices, trading volumes, and historical price information. |
| Sentiment Analysis | The analysis of text to identify sentiment, such as positive, negative, or neutral sentiment in financial news. |
| Risk Analysis | The assessment and presentation of indicators that help describe financial risk and uncertainty. |
| Forecast | An estimate of possible future outcomes based on data, models, and stated assumptions. |
| Research Assistant | A system component that helps users investigate a stock by presenting structured information and supporting explanations. |
| Functional Requirement | A requirement specifying a function or behavior that the system must provide. |
| Non-functional Requirement | A requirement specifying a quality attribute or constraint, such as performance, reliability, or usability. |



### 1.4 References

The following resources provide project documentation, source code, and contact information.

| Icon | Resource | Description |
|---|---|---|
| 📁 | [Project Repository](https://github.com/techGirl0/stock-market-analyzer) | Source code and project documentation |
| 📝 | [Project Blog](https://wolfstreeetsignalblog.wordpress.com/) | Project updates and development progress |
| ✉️ | [Contact the Team](mailto:wolfstreetsignal@gmail.com) | Team contact email address |


### 1.5 Overview

Section 2 provides an overview of the stock market analysis application, including its vision, use case diagram, and technology stack. Section 3 specifies the functional and non-functional requirements of the system, covering aspects such as functionality, usability, reliability, performance, and design constraints. Finally, Section 4 contains supporting information related to the requirements and development of the system.


## 2. Overall Description

### 2.1 Vision
WolfStreet Signal serves as a knowledgeable resource for retail investors and fintech learners. The AI provides general suggestions and explanations based on available market data, financial news, risk indicators, and documented analysis. It must not make hunch-based or unsupported speculative claims, invent facts, perform undisclosed calculations, or offer personalized investment advice. Forecasts are presented as evidence-based probabilistic scenarios with stated assumptions and uncertainty so that users can make their own informed decisions.
### 2.2 Use Case Diagram

![OUCD](/Media/UseCaseDiagram.jpg)

- Green: Planned till end of december
- Yellow: Planned till end of june

### 2.3 Technology Stack
The technology we use is:

Backend:
-Python with FastAPI

Frontend:
-Next.Js
-React
-TypeScript

AI/machine Learning:
-Python with NLP and Forcasting

IDE:
-IntelliJ and Visual Studio Code

Project Management:
-Jira
-GitHub


Deployment:
-Docker

Testing:
-pytest 
-Jest
-Cucumber
-Espresso
-JUnit
-Codacy
-CodeMR
-RestAssured

### 3.1 Functionality

The system shall provide the following functional capabilities.

#### 3.1.1 User accounts

| ID | Requirement |
| --- | --- |
| FUNC-1 | The system shall allow a user to register an account using a valid email address and password. |
| FUNC-2 | The system shall allow a registered user to log in and log out securely. |
| FUNC-3 | The system shall validate required account fields and display an actionable message when input is invalid. |
| FUNC-4 | The system shall store passwords using a secure one-way password-hashing method and shall never store them in plain text. |
| FUNC-26 | The system shall allow an authenticated user to delete their account, which shall remove the user's personal data, watchlists, portfolios, and alerts. |

#### 3.1.2 Stock search and market data

| ID | Requirement |
| --- | --- |
| FUNC-5 | The system shall allow users to search for a stock by ticker symbol or company name. |
| FUNC-6 | The system shall display the selected instrument's current or most recently available price, price change, percentage change, volume, and timestamp. While the page is open, the displayed values shall refresh at a configurable interval, within provider limits, without a full page reload. |
| FUNC-7 | The system shall display historical price data for a selected time range and interval when data is available. |
| FUNC-8 | The system shall display the source and whether market data is real-time or delayed. |
| FUNC-9 | The system shall show a clear unavailable-data message when a provider cannot return market data. |

#### 3.1.3 News and sentiment

| ID | Requirement |
| --- | --- |
| FUNC-10 | The system shall display financial news related to a selected stock or company. |
| FUNC-11 | Each news item shall display its headline, publisher, publication time, source link, and a short summary when available. The system shall not reproduce the full text of articles. |
| FUNC-12 | The system shall analyze the sentiment of each displayed news item from its headline and available summary text, and label it as positive, negative, or neutral with a score or confidence value. |
| FUNC-13 | The system shall associate news items with the relevant ticker symbols using provider-supplied tags and the queried instrument, and shall not display an association it cannot determine. |
| FUNC-14 | The system shall identify unavailable, low-confidence, or incomplete analysis rather than presenting it as a confirmed result. |

#### 3.1.4 Research, risk, and forecasting

| ID | Requirement |
| --- | --- |
| FUNC-15 | The system shall generate a structured research brief for a selected stock containing a market snapshot, recent news with a sentiment summary, risk indicators, forecast scenarios, and limitations. All figures in the brief shall come from the system's documented calculations and data sources. |
| FUNC-16 | Research briefs shall show the sources and timestamps used to produce the brief. |
| FUNC-17 | The system shall calculate and display risk indicators for a selected stock, at minimum realized volatility, maximum drawdown, beta against a documented benchmark, and a liquidity indicator, using documented input data and methodology. |
| FUNC-18 | The system shall present forecast scenarios for documented time horizons (at least one week, one month, and three months), each with a range of outcomes, stated assumptions, an uncertainty range, and a model or data timestamp. |
| FUNC-19 | The system shall not present forecasts as guarantees, personalized advice, or a single mandatory price target. |
| FUNC-20 | When the research assistant is implemented, it shall answer questions and provide general suggestions using available application data and documented analysis, clearly identify the evidence and assumptions behind its responses, and state when the requested information is unavailable or insufficient to support a conclusion. It shall not tell a user to buy, sell, or hold a specific instrument or give personalized investment advice. |

#### 3.1.5 Watchlists, portfolios, and alerts

| ID | Requirement |
| --- | --- |
| FUNC-21 | The system shall allow an authenticated user to add and remove stocks from a personal watchlist. |
| FUNC-22 | The system shall allow an authenticated user to create and view a portfolio containing selected instruments and quantities, with its current value calculated from the latest available prices. |
| FUNC-23 | The system shall allow an authenticated user to create and remove price alerts for selected instruments. |
| FUNC-24 | The system shall notify the user in the application when a configured price-alert condition is met, subject to provider availability. The notification shall state the condition that was met and shall not suggest buying or selling. |
| FUNC-25 | Watchlists, portfolios, and alerts shall be isolated between user accounts. |

### 3.2 Usability

| ID | Requirement |
| --- | --- |
| USE-1 | A first-time user shall be able to search for a stock and open its analysis from the main page without prior training. |
| USE-2 | The interface shall use consistent navigation, labels, controls, date formats, number formats, and chart conventions. |
| USE-3 | The system shall provide clear validation, loading, empty-state, and error messages for user actions. |
| USE-4 | Charts and analysis views shall include legends, units, and time ranges, and each chart shall provide a one-sentence text summary of what it shows. |
| USE-5 | The interface shall be responsive and usable on supported desktop and mobile viewport sizes, down to a width of 360 px. |
| USE-6 | The web interface shall target WCAG 2.1 Level AA, including keyboard navigation, visible focus states, sufficient colour contrast, and labels for form controls. Automated accessibility checks shall run as part of the build. A formal conformance audit is not required for the first release. |
| USE-7 | The system shall use neutral language such as "insight", "scenario", and "risk" and shall avoid wording that instructs a user to buy or sell. |
| USE-8 | Risk, sentiment, and forecast results shall provide concise contextual explanations through labels, tooltips, or linked help content. |
| USE-9 | Users shall be able to identify the age, source, and limitations of data shown on an analysis page. |

### 3.3 Reliability

| ID | Requirement |
| --- | --- |
| REL-1 | The system shall preserve user account data, watchlists, portfolios, and alerts across normal application restarts. |
| REL-2 | The system shall handle temporary provider, database, and network failures without exposing stack traces or corrupted results to users. |
| REL-3 | The system shall distinguish between unavailable, stale, partial, and successfully retrieved data. |
| REL-4 | Failed background ingestion or analysis jobs shall be logged with enough information to identify the failed operation and shall be retried automatically where safe, using a limited number of retries with increasing delays. |
| REL-5 | The system shall prevent duplicate processing from creating duplicate user alerts, news items, or stored market records. |
| REL-6 | The system shall use UTC timestamps consistently for stored data, API responses, logs, and displayed update times. |
| REL-7 | The system shall validate external data before storing or displaying it and shall not silently replace invalid values with fabricated defaults. |
| REL-8 | The system shall provide health or readiness information for required backend dependencies. |
| REL-9 | A short database backup and restoration procedure shall be documented before production deployment, and the restoration shall be rehearsed at least once. |

### 3.4 Performance

The following targets apply under the expected course-project load and shall be validated using representative test data.

| ID | Requirement |
| --- | --- |
| PERF-1 | The system shall return a successful stock search response within 2 seconds for at least 95% of requests when the required data is cached or available locally. |
| PERF-2 | The system shall return a historical chart data response within 3 seconds for at least 95% of requests under normal expected load. |
| PERF-3 | The initial analysis page shall provide visible loading feedback within 1 second and shall identify any component that is still loading. |
| PERF-4 | The system shall deliver live market updates through the supported WebSocket connection, when implemented, without requiring a full page reload. |
| PERF-5 | The system shall paginate or limit news, search, and historical-data responses so that a single request does not return an unbounded result set. |
| PERF-6 | Background ingestion, sentiment analysis, and forecast calculations shall not block interactive API requests. |
| PERF-7 | The API shall enforce configured rate limits for users and clients, and the system shall cache and throttle its calls to external providers to stay within their rate limits. |
| PERF-8 | A performance test shall record response latency, error rate, and throughput, and where practical resource usage, for a representative workload, and its results shall be documented. |

### 3.5 Supportability

| ID | Requirement |
| --- | --- |
| SUP-1 | The codebase shall be organized into separate frontend, backend, service, data-access, and provider-adapter responsibilities. |
| SUP-2 | The project shall use version control and shall keep source code, configuration templates, and documentation under Git. |
| SUP-3 | The system shall expose configuration through environment variables or documented configuration files rather than hard-coded secrets or provider credentials. |
| SUP-4 | The project shall provide setup, local-development, test, and Docker run instructions in the README. |
| SUP-5 | The project shall include automated unit tests for calculations, validation, provider adapters, and other critical business logic. |
| SUP-6 | The project shall include integration or contract tests for the core API endpoints and for each external-service boundary, using recorded provider responses where practical. |
| SUP-7 | The system shall produce structured logs for authentication events, provider failures, background jobs, and unexpected application errors without logging secrets or sensitive credentials. |
| SUP-8 | Database changes shall be made through versioned migrations, and the API shall be versioned. Both shall be reviewed together with the related code changes. |
| SUP-9 | Dependencies shall be pinned or bounded to supported versions and monitored with an automated dependency-vulnerability check, and known high-severity issues shall be resolved before a release. |
| SUP-10 | A maintainer shall be able to replace a market-data, news, or language-model provider through its adapter interface without rewriting unrelated application services. |

### 3.6 Design Constraints

| ID | Requirement |
| --- | --- |
| CON-1 | The backend shall use Python with FastAPI and the frontend shall use Next.js, React, and TypeScript as specified in section 2.3. |
| CON-2 | The system shall use REST and JSON for normal frontend-backend communication and may use WebSocket for live updates. |
| CON-3 | The system shall use UTC and ISO 8601 timestamps for persisted and exchanged date-time values. |
| CON-4 | The system shall access market-data, news, NLP, and LLM services through replaceable adapter or service interfaces. |
| CON-5 | The system shall not execute trades, connect to a broker for order placement, or provide personalized buy/sell recommendations. |
| CON-6 | The system shall communicate forecast uncertainty and shall not represent probabilistic scenarios as guaranteed future results. |
| CON-7 | The system shall respect the licensing, attribution, rate-limit, redistribution, and delayed-data requirements of every external data provider. |
| CON-8 | API keys, passwords, and other secrets shall not be committed to source control and shall be supplied through protected environment configuration. |
| CON-9 | The application shall be deployable using Docker as specified in the technology stack. |
| CON-10 | The initial implementation shall support standard web browsers and shall not require specialized client hardware. |
| CON-11 | The system shall follow the project's target standards for accessibility, web security, API documentation, and data protection described in section 3.12. |
| CON-12 | The system shall validate all external input on the server and shall access the database only through parameterized queries or an object-relational mapper, following the OWASP Top 10 guidance referenced in section 3.12. |
| CON-13 | Authentication shall use short-lived access tokens with a refresh mechanism, failed login attempts shall be rate limited, cookies carrying tokens shall be HttpOnly, Secure, and SameSite, and cross-origin access shall be restricted to an explicit allowlist. |
| CON-14 | Text received from external sources, such as news content, shall be treated as untrusted: it shall be encoded when displayed and shall never be executed or followed as instructions by any automated component. |

### 3.7 Online User Documentation and Help System Requirements

The system shall provide documentation and help so that retail investors and fintech learners can use it without prior training.

| ID | Requirement |
| --- | --- |
| DOC-1 | The system shall provide a help page that explains each main feature (stock search, market data, news, sentiment, risk indicators, forecasts). |
| DOC-2 | The system shall provide a glossary that explains financial and technical terms used in the interface (for example "sentiment score", "risk indicator", "forecast scenario"). |
| DOC-3 | The system shall show short contextual explanations (tooltips or info icons) next to risk indicators, sentiment scores and forecasts. |
| DOC-4 | Every forecast and risk view shall display a short note that results are uncertain and are not investment advice. |
| DOC-5 | The backend REST API shall be documented through an auto-generated OpenAPI page (provided by FastAPI). |
| DOC-6 | The repository shall contain a README with setup and run instructions (including Docker). |
| DOC-7 | The AI chatbot shall tell users what it can and cannot do: it provides general, evidence-based suggestions from available data and analysis, does not rely on hunches or unsupported speculation, and does not provide personalized investment advice or guaranteed price targets. Research briefs shall show their sources. |

Out of scope for now: video tutorials, a separate help-desk or chat support system.

### 3.8 Purchased Components

At this stage of the project no components are purchased.

The project uses free or open-source components and free tiers of external data services. If the project continues beyond the course, the following paid components may be considered:

- A paid market-data feed (for real-time instead of delayed prices).
- A paid news or fundamentals data provider.
- Paid usage of a large language model API for the research assistant.
- Cloud hosting for deployment.

Any purchase would require team approval and a check of the license terms (see 3.10).

### 3.9 Interfaces

#### 3.9.1 User Interfaces

- The system shall provide a web-based user interface built with Next.js, React and TypeScript.
- The interface shall be usable in current versions of common desktop browsers (Chrome, Firefox, Edge, Safari).
- The interface shall provide registration, login and logout.
- The interface shall present ticker search, the structured research brief, watchlists and alerts, portfolios, and a chat with the AI bot. Charts, news, sentiment, risk indicators and forecasts are presented as they are delivered.
- Alerts shall be described as price alerts and shall not suggest buying or selling.
- The interface shall use neutral wording such as "insights", "scenarios" and "risk", and shall avoid wording such as "you should buy".

#### 3.9.2 Hardware Interfaces

The system has no special hardware interfaces. It runs on standard server hardware (via Docker) and is accessed from standard computers with a web browser.

#### 3.9.3 Software Interfaces

| Interface | Description |
| --- | --- |
| Frontend to backend | The frontend communicates with the Python/FastAPI backend through a REST API (and WebSocket for live updates, if implemented). |
| Market data provider | The backend retrieves current and historical stock prices from an external market-data API. (tbd) |
| News provider | The backend retrieves financial news from an external news API or RSS feeds. (tbd) |
| NLP / ML components | The backend uses Python libraries for sentiment analysis and forecasting. |
| Database | The backend stores data in a database. (tbd) |
| LLM service | If the research assistant is implemented, the backend calls an external LLM API through a replaceable interface. |

The external providers shall be accessed through adapter classes so that a provider can be replaced without changing the rest of the system.

#### 3.9.4 Communications Interfaces

- All communication between browser and server shall use HTTPS.
- Data shall be exchanged in JSON format.
- Timestamps shall be stored and transmitted in UTC (ISO 8601).
- External API keys shall be stored in environment variables and never committed to the repository.

### 3.10 Licensing Requirements

- **Project license:** The team shall choose and add a license file (for example MIT) to the repository.
- **Open-source components:** All third-party libraries (for example FastAPI, React, Next.js and the NLP/ML libraries) shall only be used under their own licenses. The team shall check that these licenses allow the intended use and shall keep a list of dependencies and their licenses.
- **Data providers:** Free tiers of market and news APIs often restrict redistribution and the display of real-time exchange data. The system shall respect the terms of each provider, including rate limits and attribution rules.
- **Real-time data:** Displaying real-time exchange data publicly may require a paid license. Until one is obtained, the system shall use free or delayed data.

### 3.11 Legal, Copyright and Other Notices

- **Not investment advice:** The system is an educational and research tool. Nothing it shows is personalized investment advice, a recommendation, or a guarantee of future performance. This notice shall be visible in the interface and in the documentation.
- **Data accuracy:** Market data, news and analysis come from third-party sources and models. They may be delayed, incomplete or wrong. The team accepts no liability for decisions based on them.
- **Copyright:** (c) 2026 WolfStreet Signal team. Third-party names and trademarks belong to their owners.
- **News content:** News articles belong to their publishers. The system shall show headlines, short summaries and links to the original source rather than copying full articles.
- **Personal data:** The system provides user accounts (register, log in, log out) and stores user data such as watchlists, alerts and portfolios. This data shall be handled according to applicable data-protection law (for example GDPR). The system shall store only the data it needs, and passwords shall never be stored in plain text.
- **Legal review:** A legal review of disclaimers and interface wording would be needed before any public launch.

### 3.12 Applicable Standards

| Area | Standard or convention | How it applies |
| --- | --- | --- |
| Requirements documentation | ISO/IEC/IEEE 29148 | Structure and quality of this SRS (the template follows the Rational Unified Process SRS). |
| Software quality | ISO/IEC 25010 | Basis for the quality requirements (usability, reliability, performance, supportability). |
| Modeling | UML 2.x | Use case diagram in section 2.2. |
| Accessibility | WCAG 2.1 level AA | Target for the web interface. |
| Web security | OWASP Top 10 | Guidance for secure development of the web application and API. |
| API description | OpenAPI 3 | REST API documentation. |
| Data formats | JSON, ISO 8601 / UTC | Data exchange and timestamps. |
| Data protection | GDPR (if applicable) | Handling of any personal data. |
| Version control | Git with GitHub | All documentation and code are versioned; documentation is kept separate from code. |

## 4. Supporting Information

### 4.1 Revision History

The revision history of this document (author, date and changes) is kept in the Git commit history of this repository.

### 4.2 Excluded Features (Non-Goals)

The following are explicitly not part of the planned system:

- Trading of any kind (no buying or selling, no broker connection).
- Bank connections or payments.
- Personalized buy/sell advice. The system shows forecast scenarios and risk, never a recommendation or a single price target.
- Social features between users.
- Complex role-based access control.

Use cases without a colour in the use case diagram (section 2.2) are not planned within the project period.

### 4.3 Assumptions and Open Issues

| ID | Item | Status |
| --- | --- | --- |
| A-1 | Free or delayed data is sufficient for the first release. | Assumption |
| A-2 | Final choice of market data and news providers. | Open |
| A-3 | Choice of project license. | Open |
| A-4 | Legend of the use case diagram (section 2.2): green = planned until the end of December, yellow = planned until the end of June. | Agreed |
| A-5 | Accounts are limited to register, log in and log out, with no complex role-based access. | Assumption |

### 4.4 Related Documents

- Use case diagram: `documentation/UseCaseDiagram.png`
- Project blog: https://wolfstreeetsignalblog.wordpress.com/
