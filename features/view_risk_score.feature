Feature: View Composite Risk Score
  As a user
  I want to view a composite risk score for a selected stock
  In order to understand how risky the stock is without needing financial knowledge

  Background:
    Given I am on the homepage

  Scenario: Successfully view risk score (Happy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I navigate to the "Risk Score" section
    Then I should see a loading indicator
    And I should see a risk score between 1 and 10
    And I should see a breakdown of what is driving the score
    And each component should have a plain English explanation

  Scenario: Risk score with missing data (Unhappy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    And some risk input data is unavailable
    When I navigate to the "Risk Score" section
    Then I should see a partial risk score using available components
    And I should see a note explaining which data was missing

  Scenario: Risk score disclaimer shown (Unhappy Path)
    Given I am on the "stock dashboard" page for "AAPL"
    When I navigate to the "Risk Score" section
    Then the risk score section should include a disclaimer that this is not financial advice
