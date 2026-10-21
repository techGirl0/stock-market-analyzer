# 1 Use-Case Name
Manage Watchlist

## 1.1 Brief Description
Authenticated users can curate a personal watchlist to track preferred financial instruments. An authenticated user can add or remove stocks from their watchlist, and the system will provide targeted alerts for watchlisted items when specific conditions or news events occur.

# 2 Flow of Events
## 2.1 Basic Flow
- User clicks the "Add Stock" button while viewing a stock's dashboard.
- UI requests to add the stock to the user's watchlist.
- System saves the user's watchlist preference in the database.
- System subscribes the user to receive live, event-driven news alerts for that ticker.
- UI displays a confirmation and shows the updated watchlist.

### 2.1.1 Activity Diagram
![Manage Watchlist Activity Diagram](/documentation/Media/ManageWatchlistActivityDiagramm.jpg)

### 2.1.2 Mock-up
Design source: [Figma](https://www.figma.com/design/bBspMfnXbO5TzTM1VUkKjH)

**W1: Watchlist (list view)**

![Watchlist](</documentation/Media/W1 - Watchlist (list or read).png>)

**W2: Empty watchlist**

![Empty watchlist](</documentation/Media/W2 - Empty watchlist.png>)

**W3: Add stock dialog**

![Add stock dialog](</documentation/Media/W3 - Add stock dialog (create).png>)

**W4: Add stock error (invalid ticker)**

![Add stock error](</documentation/Media/W4 - Add stock error (invalid ticker).png>)

**W5: Remove confirmation**

![Remove confirmation](</documentation/Media/W5 - Remove confirmation (delete).png>)

**W6: Success message**

![Success message](</documentation/Media/W6 - Success message (end of use case).png>)

**CRUD:** Manage watchlist is a CRUD use case.
- Create: add stock (W3, W4, W6)
- Read: view watchlist (W1, W2)
- ~~Update~~: struck out, a watchlist entry has no editable fields
- Delete: remove stock (W5)

### 2.1.3 Narrative
```gherkin
Feature: manage watchlist

  As a signed in user
  i want to add and remove stocks from my watchlist
  in order to track my preferred stocks and receive news alerts.

  Background:
    And I am on the homepage

  Scenario: add stock to watchlist
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the "stock dashboard" page for "AAPL"
    When I press the "Add to Watchlist" button
    Then I receive a "success" message
    And "AAPL" is visible in my watchlist sidebar

  Scenario: remove stock from watchlist
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the "watchlist" page
    And "AAPL" is currently in my watchlist
    When I press the "Remove" button next to "AAPL"
    Then I receive a "success" message
    And "AAPL" is removed from my watchlist sidebar
```
    

## 2.2 Alternative Flows
### 2.2.1 Remove from Watchlist
- User navigates to their watchlist or the stock's dashboard and clicks the "Remove" button.
- User see Yes/No confirmation before deleting. 
- UI requests to remove the stock.
- System deletes the watchlist entry from the database.
- System unsubscribes the user from live alerts for that ticker.
- UI updates to show the stock has been removed.

# 3 Special Requirements
## 3.1 Data Isolation
Watchlists and alerts must be strictly isolated between user accounts. A user must never be able to view or modify another user's watchlist.

## 3.2 Compliance Rules
Watchlist UI copy and notifications must avoid personalized investment advice and banned phrases[cite: 1]. Alerts must state the condition met and never suggest buying or selling.

# 4 Preconditions
## 4.1 Login
The user has to be logged in to the system.

# 5 Postconditions
## 5.1 Watchlist Persistence
The user's updated watchlist preferences are preserved in the database and will persist across normal application restarts.
 
# 6 Extension Points
## 6.1 View Event-Driven News
When a configured alert condition is met for a watchlisted stock, the user can click the application notification to view the associated news feed.
