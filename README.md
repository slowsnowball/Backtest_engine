# Backtest Engine
1. Delete the "Parameters and functions set up manually" region.

2. Import this module.

3. Set your own parameters and functions.

Basic parameters include start_date, end_date, capital_base, freq, benchmark, universe. Tax, commission, slippage will be set to 0.001, 0.00025, 0.01 by default.

Basic functions include initialize(account) and handle_data(account). In handle_data(account) you can design your own strategy and you can define other functions to support your strategy. Ordering functions you can apply in your strategy include order_pct_to(pct_target) and order_to(target).

Function initialize(account) will be run only once when the backtest starts, and handle_data(account) will be run multiple times based on the frequency.

More functions will be added to this module in the future. :)

4. When all set up, just run your code. 