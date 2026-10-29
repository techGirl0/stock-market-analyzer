Feature: Chat with AI Bot
  As a signed in user
  I want to ask an AI assistant about stocks
  In order to receive general suggestions and understand available market data.

  Background:
    Given I am signed in with username "USER" and password "PASSWORD"
    And I am on the homepage

  Scenario: Ask a supported question (Happy Path)
    Given I am on the "AI chat" page
    When I send the message "What is the recent sentiment for AAPL?"
    Then I should see a loading indicator
    And the bot replies with an evidence-based summary of AAPL's recent news sentiment
    And the response clearly identifies the sources and assumptions

  Scenario: Ask for investment advice (Unhappy Path)
    Given I am on the "AI chat" page
    When I send the message "Should I buy AAPL right now?"
    Then the bot replies with a statement that it cannot provide personalized investment advice
    And the bot offers general market data instead

  Scenario: Query information when data is unavailable (Unhappy Path)
    Given I am on the "AI chat" page
    And market data for "UNKNOWN_CO" is unavailable
    When I send the message "What is the market cap of UNKNOWN_CO?"
    Then the bot replies stating that the requested information is unavailable
