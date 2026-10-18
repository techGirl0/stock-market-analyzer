
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
WolfStreet Signal, serves as a knowledgeable resource for retail investors and fintech learners. Our AI is designed with specific protocols: it does not engage in complex mathematical calculations, make speculative predictions about stock performances, or offer personalized investment advice. Instead, it allows users to make informed decisions by analyzing hard data, enabling them to investigate probabilistic forecasts and risk profiles with a focus on market insights.
### 2.2 Use Case Diagram

![OUCD](/documentation/UseCaseDiagram.png)

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
-Cucumber
-Espresso
-JUnit
-Codacy
-CodeMR
-RestAssured

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
| DOC-7 | The AI chat bot shall tell users what it can and cannot do (it shows scenarios and risk, and gives no personal advice or price targets), and research briefs shall show their sources. |

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
