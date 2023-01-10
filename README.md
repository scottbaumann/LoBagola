# LoBagola
*the elephants always come back*

This strategy is intended to create both long and short directional price exposure in a high volatility environment with a risk profile similar to that of a long straddle.  This strategy is designed for ES futures contracts using the Interactive Brokers API and is adaptable to other futures contracts.

## Overview

To start the trade an adaptive market buy order (Interactive Brokers market order algo) is placed on a discretionary basis (effectively random because there is no entry signal, though I prefer the first hour after the open because volume tends to be higher).  The fill price from the buy order defines `first_fill_price` which is the price above which there will be long exposure and below which there will be short exposure.

Once the long position is established there are two paths:
- Price: If the price goes X number of ticks above `first_fill_price` then a stop limit order with 2x the position size will be placed, and if that order gets triggered then the position will reverse from long to short.
- Time: If the price condition is not met then after the number of seconds defined by `wait_time` has passed then an adaptive market sell order with 2x the position size will be placed and the position will reverse from long to short.

With each position reversal the timer resets and the price conditions for the stop limit orders are dependent on whether the position is long or short.  Depending on conditions being met, the position will continue to alternate between long above `first_fill_price` and short below `first_fill_price` until the program is stopped.

## Example

Here is an example sequence of orders.  Order 1 is always a market buy order and subsequent orders are either a market order or a stop limit order, depending on which conditions are met.  This is not a Martingale system.  The position only doubles once after the first order.

| Order # | Order Type      | Quantity | Position After Fill |
| ------- | --------------  | -------- | --------            |
| 1       | market buy      | 1        |  1                  |
| 2       | stop limit sell | 2        | -1                  |
| 3       | stop limit buy  | 2        |  1                  |
| 4       | market sell     | 2        | -1                  |
| 5       | market buy      | 2        |  1                  |

## Configurable Parameters

- `wait_time` is the number of seconds counted that must be reached before a market order is placed when the price condition has not been met.  Lower volatility conditions should use a longer wait time and higher volatility conditions should use a shorter wait time.
- `quantity` is the position size.  The first adaptive market buy order is size `quantity` to establish the first long position and subsequent orders are `quantity * 2` to reverse the position.  For example, if after the first buy order of `quantity = 1` the position is long 1 contract then the time based or price based sell order (whichever happens first) will be for 2 contracts resulting in a net position of short 1 contract.

See docstrings for more advanced configurability.

## Exit

The trade is exited when `target_pnl` is reached, at which point the stop limit will adjust to be the defined number of ticks away from the current price, the trade size will adjust to equal `quanitity` so the position will close when the stop is hit rather than reverse and the order thread will stop running.

## Risk

There are two significant risks, one is in the strategy itself and the other is in order execution:

- Strategic risk: Similar to a long straddle, if the price does not move substantially above or below `first_fill_price` then there will be no profit.  Additionally, if the price whipsaws around `first_fill_price` then too many trades will be executed resulting in high trading costs.
- Execution risk: Stop limit orders are used to get better fill prices than stop orders tend to have, but the risk is that a stop limit order won't get filled at all.  In my observation this has been rare but when it happens it requires manual intervention.

