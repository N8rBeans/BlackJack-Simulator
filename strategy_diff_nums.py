from blackjack_bot import BlackjackBot, num_strategy
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # required for 3D

def format_row(hit, win_rate, profit, roi):
    return (
        f"{hit:^6}"
        f"{f'{win_rate:.2f}%':^20}"
        f"{f'{profit:>.2f} units':>25}"
        f"{f'{roi:.2f}%':>15}\n"
    )

if __name__ == "__main__":
    # run multiple trials to compare strategies
    HITS = range(2, 21)
    DECKS = range(1, 9)
    NUM_GAMES = 1000000

    # prepare to collect all results
    all_results = []

    # report text file
    txt_filename = f"results_diff_nums.txt"

    with open(txt_filename, 'w') as txtfile:
        txtfile.write("=" * 70 + "\n")
        txtfile.write("BLACKJACK STRATEGY COMPARISON\n")
        txtfile.write(f"Testing {NUM_GAMES} games per strategy\n")
        txtfile.write("=" * 70 + "\n")

    header = (
        f"{'Hit<=i':^6}"
        f"{'Win Rate':^20}"
        f"{'Profit':>25}"
        f"{'ROI':>15}\n"
    )

    ###################################################################################################

    for decks in DECKS:
        with open(txt_filename, 'a') as txtfile:
            txtfile.write("\n" + "=" * 28 + f" {decks} DECK GAME " + "=" * 29 +"\n")
            txtfile.write(header)
            txtfile.write("-" * 70 + "\n")
        
        for hit in HITS:
            bot = BlackjackBot(
                lambda g: num_strategy(g, hit),
                silent=True,
                num_decks=decks
            )

            bot.play_games(NUM_GAMES)

            win_rate = bot.stats.get_win_rate()
            profit = bot.stats.bankroll
            roi = (profit / bot.stats.total_bet * 100 if bot.stats.total_bet > 0 else 0)

            with open(txt_filename, 'a') as txtfile:
                txtfile.write(format_row(hit, win_rate, profit, roi))

            all_results.append({
                "decks": decks,
                "hit": hit,
                "win_rate": win_rate,
                "profit": profit,
                "roi": roi
            })
    
    ###################################################################################################

    print(f"Detailed report saved to: {txt_filename}")

    ###################################################################################################
    # LINE PLOT: Win Rate vs Hit Threshold (one line per deck count)
    ###################################################################################################

    fig, ax = plt.subplots(figsize=(10, 6))

    for decks in DECKS:
        xs = [r["hit"] for r in all_results if r["decks"] == decks]
        ys = [r["win_rate"] for r in all_results if r["decks"] == decks]

        ax.plot(xs, ys, label=f"{decks} deck(s)")

    ax.set_xlabel("Hit Threshold (Hit ≤ x)")
    ax.set_ylabel("Win Rate (%)")
    ax.set_title("Win Rate vs Hit Threshold for Different Shoe Sizes")
    ax.set_xticks(xs)
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig("plot_winrate_vs_hit_threshold.png", dpi=300)

    ###################################################################################################
    # 3D SURFACE PLOT: Win Rate vs Hit Threshold vs Deck Count
    ###################################################################################################

    # extract unique sorted axes
    hits = sorted(set(r["hit"] for r in all_results))
    decks = sorted(set(r["decks"] for r in all_results))

    # create grid
    H, D = np.meshgrid(hits, decks)

    # fill Z values
    Z = np.zeros_like(H, dtype=float)

    for r in all_results:
        d_idx = decks.index(r["decks"])
        h_idx = hits.index(r["hit"])
        Z[d_idx, h_idx] = r["win_rate"]  # or profit / roi

    # plot surface
    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(H, D, Z)

    ax.set_xlabel("Hit Threshold (Hit ≤ x)")
    ax.set_ylabel("Number of Decks")
    ax.set_zlabel("Win Rate (%)")
    ax.set_title("Win Rate vs Hit Threshold vs Shoe Size")

    ax.set_xticks(hits)
    ax.set_yticks(decks)

    # colorbar gives meaning to surface height
    fig.colorbar(surf, ax=ax, shrink=0.6, label="Win Rate (%)")

    plt.tight_layout()
    plt.savefig("plot_winrate_surface_plot.png", dpi=300)

    ###################################################################################################
    # AVERAGE WIN RATE ACROSS DECKS VS HIT THRESHOLD
    ###################################################################################################

    fig, ax = plt.subplots(figsize=(10, 6))

    # unique hit thresholds
    hits = sorted(set(r["hit"] for r in all_results))

    avg_win_rates = []

    for hit in hits:
        win_rates = [r["win_rate"] for r in all_results if r["hit"] == hit]
        avg_win_rates.append(sum(win_rates) / len(win_rates))

    ax.plot(hits, avg_win_rates)

    ax.set_xlabel("Hit Threshold (Hit ≤ x)")
    ax.set_ylabel("Average Win Rate (%)")
    ax.set_title("Average Win Rate vs Hit Threshold (Averaged Across Deck Counts)")
    ax.set_xticks(hits)
    ax.grid(True)

    plt.tight_layout()
    plt.savefig("plot_avg_winrate_vs_hit_threshold.png", dpi=300)
