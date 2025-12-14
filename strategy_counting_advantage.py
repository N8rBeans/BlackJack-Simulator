from blackjack_bot import BlackjackBot, num_strategy, basic_strategy, card_counting_strategy
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # required for 3D

def format_row(decks, win_rate, profit, roi):
    return (
        f"{decks:^6}"
        f"{f'{win_rate:.2f}%':^20}"
        f"{f'{profit:>.2f} units':>25}"
        f"{f'{roi:.2f}%':>15}\n"
    )

if __name__ == "__main__":
    DECKS = range(1, 9)
    NUM_GAMES = 10000000
    
    # prepare to collect all results
    all_results = []
    
    # report text file
    txt_filename = f"results_counting_decks.txt"

    with open(txt_filename, 'w') as txtfile:
        txtfile.write("=" * 70 + "\n")
        txtfile.write("BLACKJACK STRATEGY COMPARISON\n")
        txtfile.write(f"Testing {NUM_GAMES} games per strategy\n")
        txtfile.write("=" * 70 + "\n")

    header = (
        f"{'Decks':^6}"
        f"{'Win Rate':^20}"
        f"{'Profit':>25}"
        f"{'ROI':>15}\n"
    )

    ###################################################################################################

    # simple num strategy

    with open(txt_filename, 'a') as txtfile:
        txtfile.write("\n" + "=" * 24 + f" SIMPLE NUM STRATEGY " + "=" * 25 +"\n")
        txtfile.write(header)
        txtfile.write("-" * 70 + "\n")

    for decks in DECKS:        
        bot = BlackjackBot(
            lambda g: num_strategy(g, 15),
            silent=True,
            num_decks=decks
        )

        bot.play_games(NUM_GAMES)

        win_rate = bot.stats.get_win_rate()
        profit = bot.stats.bankroll
        roi = (profit / bot.stats.total_bet * 100 if bot.stats.total_bet > 0 else 0)

        with open(txt_filename, 'a') as txtfile:
            txtfile.write(format_row(decks, win_rate, profit, roi))

        all_results.append({
            "strategy": "num_15",
            "decks": decks,
            "win_rate": win_rate,
            "profit": profit,
            "roi": roi
        })
    
    # basic strategy

    with open(txt_filename, 'a') as txtfile:
        txtfile.write("\n" + "=" * 28 + f" BASIC STRATEGY " + "=" * 29 +"\n")
        txtfile.write(header)
        txtfile.write("-" * 70 + "\n")

    for decks in DECKS:
        bot = BlackjackBot(
            basic_strategy,
            silent=True,
            num_decks=decks
        )

        bot.play_games(NUM_GAMES)

        win_rate = bot.stats.get_win_rate()
        profit = bot.stats.bankroll
        roi = (profit / bot.stats.total_bet * 100 if bot.stats.total_bet > 0 else 0)

        with open(txt_filename, 'a') as txtfile:
            txtfile.write(format_row(decks, win_rate, profit, roi))

        all_results.append({
            "strategy": "basic",
            "decks": decks,
            "win_rate": win_rate,
            "profit": profit,
            "roi": roi
        })
    
    # card counting strategy

    with open(txt_filename, 'a') as txtfile:
        txtfile.write("\n" + "=" * 24 + f" CARD COUNTING STRATEGY " + "=" * 25 +"\n")
        txtfile.write(header)
        txtfile.write("-" * 70 + "\n")

    for decks in DECKS:
        bot = BlackjackBot(
            card_counting_strategy,
            silent=True,
            use_card_counting=True,
            num_decks=decks
        )

        bot.play_games(NUM_GAMES)

        win_rate = bot.stats.get_win_rate()
        profit = bot.stats.bankroll
        roi = (profit / bot.stats.total_bet * 100 if bot.stats.total_bet > 0 else 0)

        with open(txt_filename, 'a') as txtfile:
            txtfile.write(format_row(decks, win_rate, profit, roi))

        all_results.append({
            "strategy": "counting",
            "decks": decks,
            "win_rate": win_rate,
            "profit": profit,
            "roi": roi
        })
    
    ###################################################################################################

    print(f"Detailed report saved to: {txt_filename}")

    ###################################################################################################
    # LINE PLOT: Win Rate vs Number of Decks (one line per strategy)
    ###################################################################################################

    fig, ax = plt.subplots(figsize=(10, 6))

    strategies = sorted(set(r["strategy"] for r in all_results))

    for strat in strategies:
        strat_results = [r for r in all_results if r["strategy"] == strat]
        
        xs = [r["decks"] for r in strat_results]
        ys = [r["win_rate"] for r in strat_results]

        ax.plot(xs, ys, label=strat)

    ax.set_xlabel("Number of Decks in Shoe (N)")
    ax.set_ylabel("Win Rate (%)")
    ax.set_title("Win Rate vs Shoe Size by Strategy")
    ax.set_xticks(list(DECKS))
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig("plot_winrate_vs_num_decks.png", dpi=300)

    ###################################################################################################
    # LINE PLOT: Profit vs Number of Decks (one line per strategy)
    ###################################################################################################

    fig, ax = plt.subplots(figsize=(10, 6))

    strategies = sorted(set(r["strategy"] for r in all_results))

    for strat in strategies:
        strat_results = [r for r in all_results if r["strategy"] == strat]
        strat_results.sort(key=lambda r: r["decks"])

        xs = [r["decks"] for r in strat_results]
        ys = [r["profit"] for r in strat_results]

        ax.plot(xs, ys, label=strat)

    ax.set_xlabel("Number of Decks in Shoe (N)")
    ax.set_ylabel("Total Profit (Units)")
    ax.set_title("Total Profit vs Shoe Size by Strategy")
    ax.set_xticks(list(DECKS))
    ax.axhline(0, color='r', linestyle='--', linewidth=2) # zero-profit reference
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig("plot_profit_vs_num_decks.png", dpi=300)