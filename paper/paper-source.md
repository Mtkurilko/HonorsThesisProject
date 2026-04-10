---
title: "Post-Quantum Cryptography in Practice: Benchmarking, Protocol Integration, and Migration Strategy for Real Systems"
author: "Michael Kurilko"
date: "May 16th, 2026"
bibliography: references.bib
csl: ieee.csl
abstract: |
  This thesis investigates how post-quantum cryptography (PQC) can be integrated into real software systems without unacceptable operational cost. Motivated by the cryptographic risk posed by large-scale quantum computing, we evaluate the systems impact of NIST-standardized primitives—ML-KEM (FIPS 203) and ML-DSA (FIPS 204)—against widely deployed classical schemes based on RSA and elliptic curves. We implement a reproducible benchmarking framework spanning both microbenchmarks (key exchange, signing, verification, key/signature size) and application-oriented workloads (session messaging and file-transfer scenarios), with optional hybrid handshakes that combine classical and PQ secrets.

  Results show clear tradeoffs: PQ and hybrid modes substantially improve quantum resilience but increase transmission size and, in some configurations, handshake overhead. At the same time, workload-level throughput can remain competitive when session reuse and crypto-agile abstraction layers are applied. Building on these findings, we propose a practical migration strategy organized into phased hybrid deployment, interface-level crypto agility, and operational governance steps for enterprise adoption.

  The thesis contributes (1) an empirical, systems-focused evaluation of PQ integration costs, (2) a repeatable methodology for comparing classical, PQ, and hybrid configurations, and (3) a deployment-oriented migration framework that balances security modernization with engineering feasibility.
link-citations: true
filters:
  - pandoc-crossref
---

# Introduction

## The Quantum Threat

Public-key cryptography is one of the quiet assumptions behind almost every modern system. TLS handshakes, software updates, identity infrastructure, cloud APIs, and secure messaging all rely on the hardness of number-theoretic problems used by RSA and elliptic-curve cryptography (ECC). If cryptographically relevant quantum computers become practical, that assumption changes. Shor’s algorithm would make the core asymmetric primitives behind RSA and ECC computationally insecure, which means confidentiality and authenticity guarantees built on those primitives would fail.

The practical concern is not only "the day quantum arrives." It is also the *harvest now, decrypt later* model: encrypted traffic collected today can be stored and decrypted in the future once capable quantum hardware exists. That risk is especially relevant for long-lived secrets (health records, legal records, financial history, and government data), where confidentiality requirements outlast current key lifetimes.

## Why RSA/ECC Fail

RSA depends on the hardness of factoring large integers, while ECC depends on the hardness of the elliptic curve discrete logarithm problem. On classical hardware, both are hard at current key sizes. On large enough quantum hardware, they are not. In other words, the issue is not that RSA and ECC are currently “broken,” but that their *security margin is not future-proof* under the quantum threat model.

This creates an engineering problem, not just a mathematical one. Systems cannot simply “swap algorithms” overnight. Public keys, signatures, handshake flows, certificate handling, and wire formats are all tied to protocol and implementation details. The migration path must therefore address both cryptographic correctness and operational reality.

## Research Goals

This thesis focuses on a systems-level question:

> How can NIST-selected post-quantum primitives be integrated into real application workflows while keeping performance and deployment risk manageable?

The project has three goals:

1. **Measure practical overhead** of classical, post-quantum, and hybrid choices using repeatable benchmarks.
2. **Evaluate integration behavior** in workload-like scenarios (messaging sessions and file-transfer sessions), not only microbenchmarks.
3. **Propose a migration strategy** that is implementable in staged enterprise environments.

### Motivation and What I Learned

I chose this topic after exploring current technology problems that felt both important and genuinely interesting to me. I wanted something that blended math and computer science, and post-quantum cryptography stood out because it has both deep theory and real-world urgency. A conversation I had with someone else who was also interested in PQC helped push me toward focusing this thesis on practical migration, not just cryptographic concepts.

The biggest thing I learned is that PQC has many strong advantages, but adoption is not as simple as picking a new algorithm and replacing the old one. Prioritizing migration now is important, especially for long-lived sensitive data, but the transition has to be engineered carefully around system constraints. In practice, the hardest parts are often where overhead shows up (handshake latency, payload size, protocol compatibility, and operations), and this project taught me that successful migration depends on measured tradeoffs, phased rollout, and crypto-agile design choices.

# Cryptographic Background

## Classical

Classical public-key cryptography in this project is represented by RSA and ECC:

- **RSA** is used as a familiar baseline with broad legacy deployment.
- **ECC** (ECDH/ECDSA) is used as the modern classical baseline due to better performance and smaller key/signature sizes than RSA in many deployments.

These baselines are useful because migration decisions are comparative. Teams rarely deploy PQC into an empty system; they replace or layer over existing RSA/ECC-based designs.

## Lattice Cryptography Explanation

Lattice-based cryptography provides one of the strongest current candidates for quantum-resistant public-key systems. In simplified terms, lattice problems are built around high-dimensional geometric structures where finding a hidden short vector is computationally difficult. Current best-known attacks against the selected lattice problems are believed to remain hard for both classical and quantum adversaries at practical parameter sizes.

This work evaluates two NIST-standardized lattice families:

- **ML-KEM (FIPS 203)** for key establishment.
- **ML-DSA (FIPS 204)** for digital signatures.

## LWE Intuition

Learning With Errors (LWE) can be explained intuitively as follows: you see many linear equations, but each equation has a small random noise term added. Without noise, solving the system is straightforward. With noise, recovering the hidden structure becomes hard in high dimensions. Much of modern lattice cryptography leverages this "structured equations + controlled error" model to build encryption and key establishment schemes.

The key idea for systems engineers is simple: LWE-based constructions buy quantum resistance at the cost of larger objects (public keys, ciphertexts, signatures) and sometimes higher computational overhead. This thesis measures those tradeoffs in concrete workloads.

# PQC Standards

## ML-KEM (FIPS 203)

ML-KEM is used as the post-quantum key establishment primitive in this project. In implementation terms, it is integrated through a KEM interface and evaluated against RSA- and ECDH-style key exchange behavior in both microbenchmarks and session-oriented workloads.

In this framework, ML-KEM generally shows very low handshake latency but higher transmitted bytes compared with ECDH.

## ML-DSA (FIPS 204)

ML-DSA is used as the post-quantum signature primitive and compared directly with ECDSA. The benchmark design separately measures sign latency, verify latency, and signature size.

The measured pattern is consistent with expected tradeoffs: ML-DSA verification is very fast, while signature sizes are substantially larger than ECDSA.

# System Design

## Framework Architecture

The implementation is organized into three layers:

1. **Crypto layer** (`crypto/`): RSA, ECC, ML-KEM, ML-DSA, and hybrid KEX support through a common interchangeable interface.
2. **Benchmark layer** (`benchmarks/`): repeatable measurement scripts for key exchange, signatures, and refined cross-workload experiments.
3. **Workload layer** (`workloads/`): TLS-like handshake simulation, secure messaging sessions, and secure file-transfer sessions.

This separation made it possible to test algorithm substitutions without rewriting workload logic, which is a practical model for crypto-agile system design.

## Workload Model

Two workload classes were used to move beyond isolated microbenchmarks:

- **Messaging sessions:** repeated encrypted message processing under configurable session reuse.
- **File transfer:** chunked transfer pipeline with optional renegotiation points.

The workloads report latency components, throughput, transmission bytes, and memory behavior, so overhead can be localized (setup vs steady state).

The project also includes an implemented **hybrid key exchange mode** (`HYBRID (ECC+KYBER)`) that derives session key material from both classical (ECC) and post-quantum (KYBER) shared secrets.

## Experimental Methodology

The methodology combines:

- **Microbenchmarks:** key exchange latency/CPU/size, signature sign/verify/size.
- **Application-oriented runs:** messaging and file-transfer metrics under repeated sessions.
- **Raw + summary exports:** all benchmark scripts export machine-readable CSV artifacts for later plotting and interpretation.

Plots and initial findings are generated from the benchmark outputs through a reproducible analysis pipeline (`analysis/plots.py`), with figure export in PNG/PDF/SVG for publication workflows.

# Benchmark Results

## Graphs

The strongest comparison figures produced in this work are:

- `key_exchange_tradeoff` (latency vs transmission size)
- `signature_comparison` (sign, verify, size)
- `messaging_system_view` (throughput and latency components)
- `file_transfer_comparison` (throughput and setup cost)
- `hybrid_overhead` (hybrid-specific latency and bytes)

These figures were selected because they show not only which primitive is faster, but *where* each design imposes cost.

![Key Exchange Tradeoff: Latency vs Transmission Size](images/key_exchange_tradeoff.png){width=3.25in}

![Signature Comparison: Sign/Verify Latency and Signature Size](images/signature_comparison.png){width=3.25in}

![Messaging System View: Throughput and Latency Components](images/messaging_system_view.png){width=3.25in}

![File Transfer Comparison: Throughput and Handshake Setup Cost](images/file_transfer_comparison.png){width=3.25in}

![Hybrid Overhead: Handshake Latency and Transmission Bytes](images/hybrid_overhead.png){width=3.25in}

## Comparisons

At the current stage, results show a consistent pattern:

- **Key exchange:** ML-KEM has very low handshake latency; ECDH has the smallest transmission footprint; RSA has the largest setup latency.
- **Signatures:** ECDSA remains compact and fast to sign; ML-DSA verifies much faster but with significantly larger signatures.
- **Messaging and file transfer:** once sessions are established, throughput differences narrow; handshake/setup behavior dominates many practical tradeoffs.
- **Hybrid mode:** hybrid KEX incurs larger payloads and moderate setup overhead compared with single-scheme options, but provides a transition-friendly security posture.

These outcomes reinforce the idea that algorithm choice should be tied to workload and risk profile, not one-dimensional speed rankings.

## Analysis

Three conclusions are central:

1. **Setup overhead and payload growth are the main migration costs.**
2. **Steady-state throughput can remain competitive with careful session design.**
3. **Hybrid deployment is operationally useful as a transition strategy, even when not optimal in every metric.**

For engineering teams, this means migration should prioritize protocol paths where long-term confidentiality matters most and where handshake overhead can be amortized.

# Integration Challenges

## Bandwidth Inflation

Post-quantum and hybrid schemes increase key and ciphertext/signature sizes. This affects handshake packets, storage of key material, and transport-level behavior in constrained links. In practical terms, the cost is often acceptable in data center environments but can be significant in edge or mobile contexts.

## Key Storage

Larger public keys and signatures alter key-management assumptions. Certificate chains, trust stores, and cache layers must be validated for size growth. Operationally, this can require updates to limits, schemas, and telemetry thresholds rather than only cryptographic code changes.

## Protocol Redesign

Some protocol paths assume specific key formats or message sizes. Integrating PQC therefore requires interface updates, handshake message redesign, and explicit negotiation strategy (classical, PQ, hybrid). The project’s crypto-agile abstractions were useful for isolating these changes.

# Migration Framework

## The Proposed Roadmap

Based on the implementation and measured behavior, a practical roadmap is:

1. **Instrument first:** establish baseline metrics for current RSA/ECC deployments.
2. **Introduce crypto-agility layer:** make algorithm selection explicit and testable at interface boundaries.
3. **Deploy hybrid in priority channels:** start where confidentiality horizon is longest and rollback risk is manageable.
4. **Validate operational constraints:** monitor handshake latency, transmission growth, and memory impacts.
5. **Phase to PQ-default where justified:** move from hybrid to PQ-preferred configurations as ecosystem maturity increases.

This phased model reduces migration risk while preserving forward security goals.

# Discussion & Future Work

This project demonstrates that PQ migration is feasible with disciplined measurement and interface-driven design, but it also has limits. Current results are tied to this framework, parameter settings, and host environment. Broader external validity requires repeated runs across network conditions, hardware classes, and protocol stacks.

Future work includes:

- adding larger-scale statistical runs and confidence intervals,
- extending workload diversity (e.g., API gateways, service meshes, IoT constraints),
- integrating certificate-path and PKI lifecycle analysis,
- and evaluating additional standardized or emerging primitives where relevant.

The broader takeaway is practical: the quantum transition should be treated as a systems engineering program, not only a cryptographic substitution task.

# Acknowledgements

I would like to thank my Honors Thesis advisor, Dr. Joseph Kirtland, for his continous support on this project from explaining the barebone mathmatical theory to helping brainstorm the direction of the paper.

# References
