import sys
from pathlib import Path

import matplotlib.pyplot as plt
from vcdvcd import VCDVCD

SIGNALS = [
    ("wr_reset", "wr_reset", "digital"),
    ("rd_reset", "rd_reset", "digital"),
    ("wr_en", "wr_en", "digital"),
    ("rd_en", "rd_en", "digital"),
    ("full", "full", "digital"),
    ("empty", "empty", "digital"),
    ("wr_data", "wr_data", "bus"),
    ("rd_data", "rd_data", "bus"),
    ("wr_ptr", "wr_ptr", "bus"),
    ("rd_ptr", "rd_ptr", "bus"),
]

TIMESCALE_TO_NS = {
    "1 s": 1e9, "1 ms": 1e6, "1 us": 1e3, "1 ns": 1,
    "1 ps": 1e-3, "1 fs": 1e-6,
}


def find_signal(vcd, top, name):
    for ref in vcd.references_to_ids:
        base = ref.split("[")[0]
        if base == f"{top}.{name}" or base.endswith(f".{name}"):
            return vcd.references_to_ids[ref]
    return None


def to_ns(vcd):
    ts = vcd.timescale
    unit = f"{ts['magnitude']} {ts['unit']}"
    return TIMESCALE_TO_NS.get(unit, 1)


def digital_steps(tv, end_time):
    times, values = [0.0], [0]
    for t, v in tv:
        try:
            bit = int(v, 2) if v not in ("x", "z") else values[-1]
        except ValueError:
            bit = values[-1]
        times.append(t)
        values.append(bit)
    times.append(end_time)
    values.append(values[-1])
    return times, values


def bus_transitions(tv, end_time, width):
    width = int(width)
    hex_digits = max(1, -(-width // 4))
    points = [(0.0, 0)]
    for t, v in tv:
        try:
            val = int(v, 2)
        except ValueError:
            val = points[-1][1]
        points.append((t, val))
    points.append((end_time, points[-1][1]))
    return points, hex_digits


def plot_digital(ax, times, values, label):
    ax.step(times, values, where="post", color="#3b6fa0", linewidth=1.2)
    ax.fill_between(times, values, step="post", color="#3b6fa0", alpha=0.25)
    ax.set_ylim(-0.15, 1.35)
    ax.set_yticks([0, 1])
    ax.set_ylabel(label, rotation=0, ha="right", va="center")
    ax.grid(True, axis="x", alpha=0.3)


def plot_bus(ax, points, hex_digits, label, end_time, max_labels=25):
    times = [p[0] for p in points]
    values = [p[1] for p in points]
    ax.step(times, values, where="post", color="#c07a1e", linewidth=1.2)
    ax.set_ylabel(label, rotation=0, ha="right", va="center")
    ax.grid(True, axis="x", alpha=0.3)

    min_gap = end_time / max_labels if end_time else 0
    last_labeled = -min_gap
    for i in range(1, len(points)):
        if points[i][1] != points[i - 1][1]:
            t, v = points[i]
            if t - last_labeled < min_gap:
                continue
            last_labeled = t
            ax.annotate(f"0x{v:0{hex_digits}x}", xy=(t, v),
                        xytext=(2, 4), textcoords="offset points",
                        fontsize=7, rotation=45, ha="left")


def render(vcd_path, out_path, title):
    vcd = VCDVCD(vcd_path)
    top = next(iter(vcd.references_to_ids)).split(".")[0]
    scale = to_ns(vcd)
    end_time = vcd.endtime * scale

    rows = []
    for name, label, kind in SIGNALS:
        sig_id = find_signal(vcd, top, name)
        if sig_id is None:
            continue
        raw_tv = vcd.data[sig_id].tv
        tv = [(t * scale, v) for t, v in raw_tv]
        rows.append((label, kind, tv, vcd.data[sig_id].size))

    fig, axes = plt.subplots(len(rows), 1, figsize=(11, 1.1 * len(rows)),
                              sharex=True)
    if len(rows) == 1:
        axes = [axes]

    for ax, (label, kind, tv, width) in zip(axes, rows):
        if kind == "digital":
            times, values = digital_steps(tv, end_time)
            plot_digital(ax, times, values, label)
        else:
            points, hex_digits = bus_transitions(tv, end_time, width)
            plot_bus(ax, points, hex_digits, label, end_time)

    axes[-1].set_xlabel("time (ns)")
    axes[0].set_title(title)
    fig.tight_layout()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3, 4):
        print("usage: render_waveforms.py <dump.vcd|dump.fst> [out.png] [title]")
        sys.exit(1)

    vcd_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else str(Path(vcd_path).with_suffix(".png"))
    title = sys.argv[3] if len(sys.argv) > 3 else Path(vcd_path).stem

    render(vcd_path, out_path, title)
