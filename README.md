
# Pit Trading Competition Platform  

The Pit Trading Competition Platform is a specialized Django web application designed to facilitate virtual stock trading competitions among participants. This peer-to-peer trading system enforces structured trading rules while providing real-time portfolio tracking, transaction management, and dynamic leaderboard updates.

## Project Overview  

Developed for TRADERS@BPHC's trading competition, this platform simulates market dynamics through constrained trading mechanics. Participants engage in bilateral transactions under price caps (±20% of current stock prices), with automated brokerage fee calculations (0.5% per trade). The system maintains competitive integrity through transaction limits (max 5 trades per participant pair) and minimum activity requirements (12 transactions).

## Key Features  

### Transaction Management System  
Transactions follow a request-acceptance workflow where buyers and sellers negotiate prices within algorithmic boundaries. The platform validates each trade against:  
- Account balances for buyers  
- Stock inventories for sellers  
- Historical transaction counts between participant pairs
- Real-time updates modify user portfolios after trade acceptance, adjusting balances and stock holdings while applying brokerage fees automatically.

### User Authentication Framework  
Access control integrates Google OAuth with an allowlist system, restricting participation to pre-approved emails. Upon registration, users receive unique identification codes for transaction targeting. The system enforces session termination during maintenance periods through Django's session management utilities.

### Financial Tracking Mechanics  
Portfolio valuations combine liquid balances with mark-to-market stock valuations using current prices. The leaderboard algorithm activates after users complete minimum transactions, calculating net worth.

Real-time AJAX updates provide continuous portfolio value refreshes without page reloads.

### Administrative Controls  
Competition organizers can:  
1. Modify stock price parameters through Django admin  
2. Broadcast news updates to all participants  
3. Enable maintenance mode with automated user logout 
4. Monitor last traded prices using IQR-filtered weighted averages  

## Project Structure  

### Database Architecture  
The model layer implements competition logic through:  
- **Player**: Trades balances and stock inventories across 8 equities 
- **Transaction**: Records bilateral trades with status tracking  
- **Stock**: Stores price data with automated cap calculations  
- **Leaderboard**: Ranks participants by computed net worth  

### Core Functionality  
Business logic in `views.py` handles:  
- Trade validation against account balances and inventory  
- Transaction request routing between participants  
- Portfolio value calculations  
- Leaderboard eligibility checks  

## Competition Rules Implementation  
The platform codifies competition parameters from the rulebook:  
- **Starting Capital**: ₹20,000 initial balance  
- **Transaction Limits**: 5 trades max per participant pair  
- **Price Constraints**: ±20% deviation from reference prices  
- **Brokerage Fees**: 0.5% deduction on trade values  
Winners are determined by net worth after completing 12+ valid transactions.

## Technical Specifications  
- **Framework**: Django 5.1.2  
- **Authentication**: django-allauth with Google OAuth  
- **Data Analysis**: numpy for LTP calculations  
- **Real-Time Updates**: AJAX polling for portfolio refreshes  

