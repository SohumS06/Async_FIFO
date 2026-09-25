import sys
from pathlib import Path

import matplotlib.pyplot as plt
from vcdvcd import VCDVCD

SIGNALS = [
    "Asynch_FIFO.wr_clk",
    "Asynch_FIFO.rd_clk",
    "Asynch_FIFO.wr_reset",
    "Asynch_FIFO.rd_reset",
    "Asynch_FIFO.wr_en",
    "Asynch_FIFO.rd_en",
    "Asynch_FIFO.wr_data",
    "Asynch_FIFO.rd_data",
    "Asynch_FIFO.full",
    "Asynch_FIFO.empty",
    "Asynch_FIFO.wr_ptr",
    "Asynch_FIFO.rd_ptr",
]


def to_steps(tv, end_time):
    times = [0]
    values = [0]
    for t, v in tv:
        try:
            v = int(v, 2)
        except ValueError:
            v = 0
        times.append(t)
        values.append(v)
    times.append(end_time)
    values.append(values[-1])
    return times, values


def main(vcd_path):
    vcd = VCDVCD(vcd_path)
    end_time = vcd.endtime

    signals = [name for name in SIGNALS if name in vcd.data.keys() or
               any(name in ref for ref in vcd.references_to_ids)]

    fig, axes = plt.subplots(len(signals), 1, figsize=(12, 2 * len(signals)),
                              sharex=True)
    if len(signals) == 1:
        axes = [axes]

    for ax, name in zip(axes, signals):
        sig_id = vcd.references_to_ids.get(name)
        if sig_id is None:
            continue
        tv = vcd.data[sig_id].tv
        times, values = to_steps(tv, end_time)
        ax.step(times, values, where="post")
        ax.set_ylabel(name.split(".")[-1], rotation=0, ha="right",
                       va="center")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("time (ps)")
    fig.tight_layout()

    out_path = Path(vcd_path).with_suffix(".png")
    fig.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: render_waveforms.py <dump.vcd>")
        sys.exit(1)
    main(sys.argv[1])
