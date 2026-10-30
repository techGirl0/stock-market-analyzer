# 1 Use-Case Name
Manage Portfolio

## 1.1 Brief Description
Authenticated users can create a personal portfolio to track their holdings. The user can add selected financial instruments with specified quantities and view their current holdings alongside a calculated total value based on the latest available market prices.

# 2 Flow of Events
## 2.1 Basic Flow
- User clicks the "Add Holding" button while viewing their portfolio page.
- UI presents a form to search for a ticker and enter a quantity.
- User inputs the stock ticker and the quantity they hold, then submits.
- System calculates the current value based on the latest available prices.
- System saves the user's portfolio data in the database.
- UI displays a confirmation and shows the updated portfolio with the current calculated value.

### 2.1.1 Activity Diagram
![Manage Portfolio Activity Diagram](../Media/ManagePortfolioActivityDiagramm.jpg)

### 2.1.2 Mock-up

Design source: [Figma](https://www.figma.com/design/bBspMfnXbO5TzTM1VUkKjH)

**P1: Portfolio (list view with calculated values)**

![Portfolio](</documentation/Media/P1 - Portfolio.png>)

**P2: Empty portfolio**

![Empty portfolio](</documentation/Media/P2 - Empty portfolio.png>)

**P3: Add holding dialog**

![Add holding dialog](</documentation/Media/P3 - Add holding dialog.png>)

**P4: Add holding error (invalid ticker or quantity)**

![Add holding error](</documentation/Media/P4 - Add holding error.png>)

**P5: Value unavailable (alternative flow)**

![Value unavailable](</documentation/Media/P5 - Value unavailable.png>)

**P6: Holding added (success)**

![Holding added](</documentation/Media/P6 - Holding added (success).png>)

**CRUD:** Manage portfolio is restricted to Create and Read operations for the first release.
- Create: add stock holding with quantity (P3, P4)
- Read: view portfolio and calculated values (P1, P2)
- ~~Update~~: struck out, editing a holding quantity is out of planned scope.
- ~~Delete~~: struck out, deleting portfolios or selling securities is out of planned scope.

### 2.1.3 Narrative
### 2.1.3 Narrative
```gherkin
Feature: manage portfolio

  As a signed in user
  I want to create a portfolio and add stocks with quantities
  In order to view my holdings and their current calculated value.

  Background:
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the homepage

  Scenario: add holding to portfolio successfully (Happy Path)
    Given I am on the "portfolio" page
    When I press the "Add Holding" button
    And I enter "AAPL" for the ticker and "10" for the quantity
    Then I should receive a "success" message
    And "AAPL" with quantity "10" and its calculated value should be visible in my portfolio

  Scenario: add holding fails due to invalid inputs (Unhappy Path)
    Given I am on the "portfolio" page
    When I press the "Add Holding" button
    And I enter "INVALID123" for the ticker and "-5" for the quantity
    Then I should see an "invalid ticker or quantity" error message
    And no holding should be added to my portfolio

  Scenario: market data provider unavailable for portfolio (Unhappy Path)
    Given I am on the "portfolio" page
    And the market data provider is temporarily unavailable
    When I add a holding "MSFT" with quantity "5"
    Then the holding "MSFT" is saved in my portfolio
    And I should see an "unavailable-data" message for its calculated value
```

## 2.2 Alternative Flows
### 2.2.1 Unavailable Market Data
- User adds a valid ticker to the portfolio, but the market data provider is temporarily unavailable.
- System saves the holding but cannot calculate the current value.
- UI displays the holding with a clear unavailable-data message for its current value.

# 3 Special Requirements
## 3.1 Data Isolation and Persistence
Portfolio data must be strictly isolated between user accounts. A user must never be able to view or modify another user's portfolio. Portfolio data must persist across normal application restarts.

# 4 Preconditions
## 4.1 Login
The user has to be logged in to the system.

# 5 Postconditions
## 5.1 Portfolio Persistence
The user's updated portfolio holdings are preserved in the database.

# 6 Extension Points
*(None planned for the current scope)*
