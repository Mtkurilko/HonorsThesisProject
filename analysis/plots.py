import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
GRAPHS_DIR = RESULTS_DIR / "graphs"


def _load_summary(path=RESULTS_DIR / "refined_experiment_summary.csv"):
	df = pd.read_csv(path)
	df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
	return df


def _metric_table(df, experiment):
	exp_df = df[df["Experiment"] == experiment].copy()
	return exp_df.pivot(index="Algorithm", columns="Metric", values="Value")


def _save(fig, filename):
	GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
	out_path = GRAPHS_DIR / filename
	fig.tight_layout()
	fig.savefig(out_path, dpi=300, bbox_inches="tight")
	plt.close(fig)


def _save_multi(fig, stem, formats=("png",)):
	GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
	fig.tight_layout()
	for fmt in formats:
		out_path = GRAPHS_DIR / f"{stem}.{fmt}"
		if fmt in {"pdf", "svg"}:
			fig.savefig(out_path, bbox_inches="tight")
		else:
			fig.savefig(out_path, dpi=300, bbox_inches="tight")
	plt.close(fig)


def plot_key_exchange_tradeoff(df, formats=("png",)):
	table = _metric_table(df, "key_exchange").copy()
	table = table.sort_values("latency_ms_mean")

	fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
	colors = list(plt.cm.tab10.colors)[: len(table)]

	axes[0].bar(table.index, table["latency_ms_mean"], color=colors)
	axes[0].set_title("Key Exchange Latency (Lower is Better)")
	axes[0].set_ylabel("Latency (ms)")
	axes[0].tick_params(axis="x", rotation=20)

	scatter = axes[1].scatter(
		table["tx_bytes_mean"],
		table["latency_ms_mean"],
		s=120,
		c=range(len(table)),
		cmap="viridis",
	)
	for alg, row in table.iterrows():
		axes[1].annotate(alg, (row["tx_bytes_mean"], row["latency_ms_mean"]), xytext=(5, 5), textcoords="offset points")
	axes[1].set_title("Key Exchange Tradeoff: Payload vs Latency")
	axes[1].set_xlabel("Transmission Bytes")
	axes[1].set_ylabel("Latency (ms)")
	axes[1].set_yscale("log")

	_save_multi(fig, "key_exchange_tradeoff", formats=formats)


def plot_signature_comparison(df, formats=("png",)):
	table = _metric_table(df, "signatures")
	algorithms = list(table.index)

	fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

	axes[0].bar(algorithms, table["sign_ms_mean"], color="#4e79a7")
	axes[0].set_title("Signature Generation Latency")
	axes[0].set_ylabel("ms")
	axes[0].tick_params(axis="x", rotation=20)

	axes[1].bar(algorithms, table["verify_ms_mean"], color="#59a14f")
	axes[1].set_title("Signature Verification Latency")
	axes[1].set_ylabel("ms")
	axes[1].tick_params(axis="x", rotation=20)

	axes[2].bar(algorithms, table["signature_size_bytes_mean"], color="#f28e2b")
	axes[2].set_title("Signature Size")
	axes[2].set_ylabel("Bytes")
	axes[2].tick_params(axis="x", rotation=20)

	_save_multi(fig, "signature_comparison", formats=formats)


def plot_messaging_system_view(df, formats=("png",)):
	table = _metric_table(df, "messaging").copy()
	table = table.sort_values("messages_per_sec", ascending=False)

	fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

	axes[0].bar(table.index, table["messages_per_sec"], color="#4e79a7")
	axes[0].set_title("Messaging Throughput")
	axes[0].set_ylabel("Messages/sec")
	axes[0].tick_params(axis="x", rotation=20)

	width = 0.35
	x = range(len(table.index))
	axes[1].bar([i - width / 2 for i in x], table["handshake_latency_ms_mean"], width=width, label="Handshake ms", color="#f28e2b")
	axes[1].bar([i + width / 2 for i in x], table["message_latency_ms_mean"], width=width, label="Per-message ms", color="#59a14f")
	axes[1].set_xticks(list(x))
	axes[1].set_xticklabels(table.index, rotation=20)
	axes[1].set_title("Messaging Latency Components")
	axes[1].set_ylabel("ms")
	axes[1].legend()
	axes[1].set_yscale("log")

	_save_multi(fig, "messaging_system_view", formats=formats)


def plot_file_transfer_comparison(df, formats=("png",)):
	table = _metric_table(df, "file_transfer").copy()
	table = table.sort_values("throughput_mbps_mean", ascending=False)

	fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

	axes[0].bar(table.index, table["throughput_mbps_mean"], color="#4e79a7")
	axes[0].set_title("File Transfer Throughput")
	axes[0].set_ylabel("Mbps")
	axes[0].tick_params(axis="x", rotation=20)

	axes[1].scatter(table["tx_bytes_mean"], table["handshake_latency_ms_mean"], s=120, color="#e15759")
	for alg, row in table.iterrows():
		axes[1].annotate(alg, (row["tx_bytes_mean"], row["handshake_latency_ms_mean"]), xytext=(5, 5), textcoords="offset points")
	axes[1].set_title("File Transfer Setup Cost")
	axes[1].set_xlabel("Handshake Transmission Bytes")
	axes[1].set_ylabel("Handshake Latency (ms)")
	axes[1].set_yscale("log")

	_save_multi(fig, "file_transfer_comparison", formats=formats)


def plot_hybrid_overhead(df, formats=("png",)):
	table = _metric_table(df, "hybrid_overhead").copy()
	table = table.loc[[idx for idx in ["ECC", "KYBER", "HYBRID"] if idx in table.index]]

	fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

	axes[0].bar(table.index, table["handshake_latency_ms_mean"], color="#76b7b2")
	axes[0].set_title("Hybrid Overhead: Handshake Latency")
	axes[0].set_ylabel("ms")
	axes[0].set_yscale("log")

	axes[1].bar(table.index, table["tx_bytes_mean"], color="#edc948")
	axes[1].set_title("Hybrid Overhead: Handshake Transmission")
	axes[1].set_ylabel("Bytes")

	_save_multi(fig, "hybrid_overhead", formats=formats)


def _ratio(a, b):
	return (a / b) if b else float("inf")


def write_initial_findings(df, output_path=RESULTS_DIR / "initial_findings.md"):
	kex = _metric_table(df, "key_exchange")
	sig = _metric_table(df, "signatures")
	msg = _metric_table(df, "messaging")
	ftx = _metric_table(df, "file_transfer")
	hyb = _metric_table(df, "hybrid_overhead")

	fastest_kex = kex["latency_ms_mean"].idxmin()
	smallest_kex = kex["tx_bytes_mean"].idxmin()

	fastest_sign = sig["sign_ms_mean"].idxmin()
	fastest_verify = sig["verify_ms_mean"].idxmin()
	smallest_sig = sig["signature_size_bytes_mean"].idxmin()

	best_msg_tp = msg["messages_per_sec"].idxmax()
	best_msg_handshake = msg["handshake_latency_ms_mean"].idxmin()

	best_ftx_tp = ftx["throughput_mbps_mean"].idxmax()
	best_ftx_handshake = ftx["handshake_latency_ms_mean"].idxmin()

	hybrid_latency = hyb.loc["HYBRID", "handshake_latency_ms_mean"] if "HYBRID" in hyb.index else None
	ecc_latency = hyb.loc["ECC", "handshake_latency_ms_mean"] if "ECC" in hyb.index else None
	kyber_latency = hyb.loc["KYBER", "handshake_latency_ms_mean"] if "KYBER" in hyb.index else None

	has_hybrid = "HYBRID" in hyb.index
	has_hybrid_kex = "HYBRID (ECC+KYBER)" in kex.index

	lines = [
		"# Initial Findings",
		"",
		"## Key Exchange",
		f"- Fastest mean handshake latency: **{fastest_kex}** ({kex.loc[fastest_kex, 'latency_ms_mean']:.6f} ms).",
		f"- Smallest handshake payload: **{smallest_kex}** ({kex.loc[smallest_kex, 'tx_bytes_mean']:.1f} bytes).",
		f"- RSA latency overhead vs fastest: **{_ratio(kex.loc['RSA', 'latency_ms_mean'], kex['latency_ms_mean'].min()):.1f}x**.",
		"",
		"## Signatures",
		f"- Fastest signing: **{fastest_sign}** ({sig.loc[fastest_sign, 'sign_ms_mean']:.6f} ms).",
		f"- Fastest verification: **{fastest_verify}** ({sig.loc[fastest_verify, 'verify_ms_mean']:.6f} ms).",
		f"- Smallest signatures: **{smallest_sig}** ({sig.loc[smallest_sig, 'signature_size_bytes_mean']:.1f} bytes).",
		f"- ML-DSA verification speedup vs ECDSA: **{_ratio(sig.loc['ECDSA', 'verify_ms_mean'], sig.loc['ML-DSA (Dilithium)', 'verify_ms_mean']):.1f}x**.",
		f"- ML-DSA signature-size overhead vs ECDSA: **{_ratio(sig.loc['ML-DSA (Dilithium)', 'signature_size_bytes_mean'], sig.loc['ECDSA', 'signature_size_bytes_mean']):.1f}x**.",
		"",
		"## Messaging",
		f"- Best throughput: **{best_msg_tp}** ({msg.loc[best_msg_tp, 'messages_per_sec']:.1f} msgs/s).",
		f"- Lowest handshake latency in messaging loop: **{best_msg_handshake}** ({msg.loc[best_msg_handshake, 'handshake_latency_ms_mean']:.6f} ms).",
		f"- RSA handshake overhead vs best messaging handshake: **{_ratio(msg.loc['RSA', 'handshake_latency_ms_mean'], msg['handshake_latency_ms_mean'].min()):.1f}x**.",
		"",
		"## File Transfer",
		f"- Highest throughput: **{best_ftx_tp}** ({ftx.loc[best_ftx_tp, 'throughput_mbps_mean']:.3f} Mbps).",
		f"- Lowest setup latency: **{best_ftx_handshake}** ({ftx.loc[best_ftx_handshake, 'handshake_latency_ms_mean']:.6f} ms).",
		f"- Throughput spread across algorithms is narrow: **{ftx['throughput_mbps_mean'].max() - ftx['throughput_mbps_mean'].min():.3f} Mbps**.",
	]

	if has_hybrid_kex:
		lines.extend(
			[
				f"- Hybrid KEX latency: **{kex.loc['HYBRID (ECC+KYBER)', 'latency_ms_mean']:.6f} ms**.",
				f"- Hybrid KEX payload: **{kex.loc['HYBRID (ECC+KYBER)', 'tx_bytes_mean']:.1f} bytes**.",
				f"- Hybrid KEX latency vs ECDH: **{_ratio(kex.loc['HYBRID (ECC+KYBER)', 'latency_ms_mean'], kex.loc['ECDH', 'latency_ms_mean']):.2f}x**.",
				f"- Hybrid KEX payload vs ECDH: **{_ratio(kex.loc['HYBRID (ECC+KYBER)', 'tx_bytes_mean'], kex.loc['ECDH', 'tx_bytes_mean']):.2f}x**.",
			]
		)

	if has_hybrid:
		lines.extend(["", "## Hybrid"])

	if has_hybrid and hybrid_latency is not None and ecc_latency is not None and kyber_latency is not None:
		lines.extend(
			[
				f"- Hybrid handshake latency: **{hybrid_latency:.6f} ms**.",
				f"- Hybrid latency vs ECC: **{_ratio(hybrid_latency, ecc_latency):.2f}x**.",
				f"- Hybrid latency vs KYBER: **{_ratio(hybrid_latency, kyber_latency):.2f}x**.",
				f"- Hybrid transmission bytes: **{hyb.loc['HYBRID', 'tx_bytes_mean']:.1f}** (sum-like overhead compared with single-scheme handshakes).",
			]
		)

	lines.extend(
		[
			"",
			"## Recommendation for Paper Figures",
			"- `key_exchange_tradeoff.png`: strongest protocol tradeoff visualization (latency vs payload).",
			"- `signature_comparison.png`: clear asymmetric tradeoff between signing, verification, and size.",
			"- `messaging_system_view.png`: practical session-level behavior and handshake amortization.",
			"- `file_transfer_comparison.png`: end-to-end throughput plus setup-cost context.",
		]
	)

	if "HYBRID" in hyb.index:
		lines.append("- `hybrid_overhead.png`: dedicated evidence for hybrid construction overhead.")

	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_all_plots_and_findings(
	summary_path=RESULTS_DIR / "refined_experiment_summary.csv",
	formats=("png",),
):
	df = _load_summary(summary_path)
	plot_key_exchange_tradeoff(df, formats=formats)
	plot_signature_comparison(df, formats=formats)
	plot_messaging_system_view(df, formats=formats)
	plot_file_transfer_comparison(df, formats=formats)
	if (df["Experiment"] == "hybrid_overhead").any():
		plot_hybrid_overhead(df, formats=formats)
	write_initial_findings(df)


if __name__ == "__main__":
	generate_all_plots_and_findings()
	print("Generated graphs in results/graphs and findings in results/initial_findings.md")
