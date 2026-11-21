# Independent Audit of the Alpöge & Claude Riemann Hypothesis Lean 4 Formalization
# Alpöge & Claude 黎曼猜想 Lean 4 形式化工程独立核查仓库

[![Lean 4](https://img.shields.io/badge/Lean_4-v4.33.1-blue)](#1-verification-scorecard--核心核查总表)
[![Mathlib](https://img.shields.io/badge/Mathlib-0df444a3_(v4.33.1)-informational)](#1-verification-scorecard--核心核查总表)
[![Source SHA256](https://img.shields.io/badge/lean.tar.gz-9631b4f0…-success)](#1-verification-scorecard--核心核查总表)
[![Corpus](https://img.shields.io/badge/Files-175%2C187_(0_failed)-brightgreen)](#1-verification-scorecard--核心核查总表)
[![Theorems](https://img.shields.io/badge/Theorems-5_RH_%2F_GRH-brightgreen)](#2-the-five-target-theorems--五条核心主定理)
[![Axioms](https://img.shields.io/badge/Axioms-propext_%7C_Classical.choice_%7C_Quot.sound-success)](#1-verification-scorecard--核心核查总表)
[![MIT Kernels](https://img.shields.io/badge/MIT_nanoda_%26_con--leche-Accepted_(exit_0)-brightgreen)](#1-verification-scorecard--核心核查总表)
[![Repo Size](https://img.shields.io/badge/Audit_Repo-<1_MB_(Lightweight)-orange)](#3-three-step-local-reproduction--三步本地零门槛复现)

> **Language Navigation / 语言导览**：This root document provides a side-by-side **English & Chinese (中英双语)** overview for global developers and formal-methods auditors. For the full deep-dive reports, see:
> - 📋 **[`00-总报告-我们做了什么.md`](00-总报告-我们做了什么.md)** — Process log: how the task evolved, the evidence layers, and the corrections made along the way (339 lines)
> - 📄 **[`01-验证报告-黎曼猜想.md`](01-验证报告-黎曼猜想.md)** — Full Formal Verification & Static Security Audit Report (Chinese, 249 lines)
> - 🗺️ **[`02-中文导读与代码地图.md`](02-中文导读与代码地图.md)** — Complete Chinese Reader's Guide, 13-Hop Proof Chain & 20-Step Mathematical Code Map (733 lines)
> - 🧮 **[`03-核心13跳-人类可读数学证明.md`](03-核心13跳-人类可读数学证明.md)** — The 13-hop backbone rewritten as a human-readable LaTeX mathematics lecture, no Lean syntax (582 lines)
> - 🏗️ **[`04-AI千万行代码工程架构分析.md`](04-AI千万行代码工程架构分析.md)** — Engineering anatomy of 175,187 files: LOC distribution, Statement/Proof pairing, import DAG, generation strategy (454 lines)
> - 🔐 **[`哈希清单-SHA256.txt`](哈希清单-SHA256.txt)** — Complete SHA-256 Evidence Manifest for Official Archives, Exports, and Logs

---

## 1. Verification Scorecard / 核心核查总表

On November 10, 2026, Levent Alpöge and Claude (Opus 4.6) released a 175,187-file Lean 4 formalization proving the Riemann Hypothesis (`RH`) and Generalized Riemann Hypothesis (`GRH`) for Dirichlet L-functions (`https://alpo.ge/`). This lightweight repository (< 15 MB target, < 1 MB actual tracked text) provides zero-dependency Python 3 audit scripts, cryptographic hash manifests, and a structural code map to independently verify the formal claims without requiring a 250 GB RAM build server.

2026 年 11 月 10 日，Levent Alpöge 与 Claude (Opus 4.6) 公开了一份包含 175,187 个 Lean 4 源码文件的形式化工程，给出黎曼猜想（RH）与 Dirichlet L-函数广义黎曼猜想（GRH）的形式化证明（`https://alpo.ge/`）。本仓库作为轻量级独立审计仓库（目标体积 < 15 MB，实际纯文本约 300 KB），提供零第三方依赖的 Python 3 核查脚本、SHA-256 哈希证据链与全景代码地图，使任何开发者无需 250 GB 内存服务器即可在本地完成核验。

| Audit Dimension / 核查维度 | Verified Result / 核查结论 | Cryptographic / Log Evidence / 证据锚点 | Status / 状态 |
| :--- | :--- | :--- | :---: |
| **Source Identity**<br>源码归档一致性 | `lean.tar.gz` (239,275,554 bytes, 14 split parts `.aa`–`.an`). Byte-for-byte identical across all 175,190 files to the extracted workspace zip. | SHA-256: `9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc` | ✅ PASS |
| **Toolchain & Mathlib**<br>工具链与数学库版本 | `leanprover/lean4:v4.33.1`<br>Mathlib commit `0df444a360eaa60ab8c11dca51a86af692955474` (`v4.33.1`) | `lean-toolchain` & `lake-manifest.json`; stock Mathlib `RiemannHypothesis` at `Mathlib/NumberTheory/LSeries/RiemannZeta.lean:185` | ✅ PASS |
| **Corpus Scale & Build**<br>全库规模与编译 | **175,187** `.lean` files, **17,374,215** lines, **1,030,531,854** bytes.<br>183,903 Lake build tasks: **0 failed** (MIT & China 128-vCPU station, 6h58m31s, 210 GiB peak RAM). | `eng_stats.py` full scan; MIT `leanchecker` 175,187/175,187; `lean4lean` 175,187/175,187 | ✅ PASS |
| **Target Theorems**<br>五条主定理形式陈述 | 5 theorems in `src/Main.lean:4-12` covering `RiemannHypothesis` (Mathlib definition) and 4 Dirichlet L-function zero-location propositions in `src/Statements.lean:3-16`. | Reconstructed directly from `challenge.ndjson` AST by `decode_challenge.py` and `sorry_check.py` | ✅ PASS |
| **Axiom Hygiene**<br>公理纯净度审计 | All 5 theorems depend solely on Lean's 3 standard axioms:<br>`[propext, Classical.choice, Quot.sound]` | MIT `audit.log` (`be4301f5…`, 15 environment axioms all in `Init`, `sorryAx` unused in solution) | ✅ PASS |
| **Static Bypass Scan**<br>全库静态旁路扫描 | `sorry` / `admit`: **0** · `axiom`: **0** · `opaque`: **0** · `native_decide`: **0** · `@[extern]` / `implemented_by`: **0** · `unsafe`: **0** · `#eval` / `IO.Process`: **0** · definition shadowing: **0** | Full 175,187-file static scan (`01-验证报告-黎曼猜想.md` §3.4); 2 `addDecl` occurrences in `CutCptCopy.lean` pass kernel checking | ✅ PASS |
| **Independent Kernels (MIT)**<br>MIT 独立内核重放 | **`nanoda`** (Rust kernel): accepted in 27m42s (80 threads, 84.7 GB RSS, exit 0).<br>**`con-leche --verified`**: accepted 1,468,418 decls in 3m15s (exit 0).<br>**`con-leche --compare`**: all 5 challenge theorems justified by solution (exit 0). | `nanoda.log` (`2f93e7c3…`)<br>`con-leche-master.log` (`ef73377a…`)<br>`sutherland_conleche.log` (`9c70f6f8…`)<br>`challenge.ndjson.zst` (`c24ef99d…`) | ✅ PASS |
| **Pending Closure Items**<br>待闭环项（截至 2026-11-21） | 1. Lean default + paranoid kernel single-threaded export replay on MIT (`solution.ndjson.zst`, 61.57 GB uncompressed).<br>2. End-to-end `lake comparator` (Lean `v4.36.0`) finish (statement & axiom check already passed).<br>3. Hertaspace 256-core build (at 102,659 / 183,903 tasks, 55.8%).<br>4. Mathematical peer review of the underlying human proof. | Tracked live at `https://math.mit.edu/~drew/grh/` and `https://hertaspace.com/rh/` | ⏳ RUNNING |

---

## 2. The Five Target Theorems / 五条核心主定理

All five target theorems reside in `src/Main.lean` (12 lines total), referencing four custom `Prop` definitions in `src/Statements.lean` (16 lines total) and Mathlib's built-in `RiemannHypothesis`.

全部五条顶层定理位于 `src/Main.lean`（共 12 行），引用 `src/Statements.lean`（共 16 行）中的四个自定义命题以及 Mathlib 标准库自带的 `RiemannHypothesis`。

| # | Theorem in `src/Main.lean` | Statement Type & Formal Meaning / 类型签名与数学含义 | Proof Term / 证明项 |
| :-: | :--- | :--- | :--- |
| **1** | `riemannHypothesis`<br>(`src/Main.lean:4`) | `RiemannHypothesis` (`Mathlib/NumberTheory/LSeries/RiemannZeta.lean:185`):<br>`∀ (s : ℂ), riemannZeta s = 0 → (¬∃ n : ℕ, s = -2 * (↑n + 1)) → s ≠ 1 → s.re = 1 / 2` | `rhOfAll` |
| **2** | `riemannZeta_eq_zero_re`<br>(`src/Main.lean:6`) | `RiemannZetaZerosOnLine` (`src/Statements.lean:3-4`):<br>`∀ (s : ℂ), riemannZeta s = 0 → (∀ n : ℕ, s ≠ -2 * (↑n + 1)) → s ≠ 1 → s.re = 1 / 2`<br>*(Definitional equality `RiemannZetaZerosOnLine = RiemannHypothesis` holds by `rfl` up to quantifier rewrite)* | `rhOfAll` |
| **3** | `LFunction_ne_zero_of_half_lt_re`<br>(`src/Main.lean:8`) | `DirichletLNonvanishingRightOfHalf` (`src/Statements.lean:6-8`):<br>`∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (s : ℂ), 1 / 2 < s.re → (χ ≠ 1 ∨ s ≠ 1) → DirichletCharacter.LFunction χ s ≠ 0`<br>*(The true mathematical engine of the repository: half-plane nonvanishing `UpperTheory.EveryCharacter`)* | `allChi` |
| **4** | `LFunction_eq_zero_re`<br>(`src/Main.lean:10`) | `DirichletLZerosOnLine` (`src/Statements.lean:10-12`):<br>`∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (s : ℂ), DirichletCharacter.LFunction χ s = 0 → 0 < s.re → s.re < 1 → s.re = 1 / 2`<br>*(Critical strip zeros of arbitrary Dirichlet L-functions lie on $\operatorname{Re}(s) = 1/2$)* | `claimAll.2.1` |
| **5** | `LFunction_eq_zero_re_of_isPrimitive`<br>(`src/Main.lean:12`) | `PrimitiveDirichletLZerosOnLine` (`src/Statements.lean:14-16`):<br>`∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N), χ.IsPrimitive → ∀ (s : ℂ), DirichletCharacter.LFunction χ s = 0 → (∀ n : ℕ, s ≠ -↑n) → s ≠ 1 → s.re = 1 / 2` | `critAll` |

---

## 3. Three-Step Local Reproduction / 三步本地零门槛复现

To keep this repository under **15 MB**, the two large upstream artifacts—the **229 MB** source archive (`lean.tar.gz`) and the **45 MB** MIT challenge export (`challenge.ndjson.zst`)—are **excluded** from Git history. All 4 Python scripts in this repository use **only the Python 3 standard library** (for `.zst` decompression on Python < 3.14, either install `pip install zstandard` or have the `zstd` CLI on your `PATH`) and run unmodified on **Linux, macOS, and Windows**.

为确保本仓库总大小严格控制在 **15 MB 以内**，仓库不包含 **229 MB** 的官方源码包 `lean.tar.gz` 与 **45 MB** 的 MIT 挑战导出文件 `challenge.ndjson.zst`。本仓库的 4 个 Python 脚本全部去除本地硬编码路径与代理绑定，仅依赖 Python 3 标准库（Python 3.14 以下解压 `.zst` 可选安装 `pip install zstandard` 或使用系统 `zstd` 命令），在 **Linux / macOS / Windows** 下均可零报错运行。

Downloads and scan outputs land in two git-ignored directories, `external/` (official archives) and `analysis/` (scan reports), so a fresh clone stays clean and small. / 下载物与扫描产物分别落在 `.gitignore` 排除的 `external/` 与 `analysis/` 两个目录，克隆下来只有文本，不会被大文件污染。

### Step 1: Clone & Pull Official Artifacts / 第一步：克隆仓库并拉取官方大文件

Run the following commands in the repository root (`bash` / `zsh` / `Git Bash`):

```bash
mkdir -p external

# 1A. Download MIT challenge export (46,881,299 bytes, ~45 MB)
curl -fL https://math.mit.edu/~drew/grh/challenge.ndjson.zst -o external/challenge.ndjson.zst

# 1B. Download & concatenate the 14-part official Lean source archive from alpo.ge (239,275,554 bytes, ~229 MB)
for s in aa ab ac ad ae af ag ah ai aj ak al am an; do
  curl -fL "https://alpo.ge/lean.tar.gz.${s}" -o "external/lean.tar.gz.${s}"
done
cat external/lean.tar.gz.a[a-n] > external/lean.tar.gz
rm -f external/lean.tar.gz.a[a-n]

# 1C. Verify cryptographic SHA-256 digests against the official manifest
python -c "
import hashlib, pathlib
expected = {
    'external/lean.tar.gz': '9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc',
    'external/challenge.ndjson.zst': 'c24ef99dab3556a52c7fb886e03cf22a242f3b96f82ae4cc40539e5d2f678ac6',
}
for rel, exp in expected.items():
    p = pathlib.Path(rel)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f'{rel}: {digest}  MATCH={digest == exp}')
    assert digest == exp, f'SHA-256 mismatch for {rel}'
"
```

<details>
<summary>Windows (PowerShell) 等价写法 / Windows equivalent for steps 1A–1B</summary>

```powershell
New-Item -ItemType Directory -Force external | Out-Null

# 1A. MIT challenge export
Invoke-WebRequest -Uri 'https://math.mit.edu/~drew/grh/challenge.ndjson.zst' `
  -OutFile 'external/challenge.ndjson.zst'

# 1B. 14 split parts from alpo.ge
'aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al','am','an' | ForEach-Object {
  Invoke-WebRequest -Uri "https://alpo.ge/lean.tar.gz.$_" -OutFile "external/lean.tar.gz.$_"
}

# 1B'. Byte-wise concatenation (cmd has no PowerShell equivalent)
$ms = [IO.MemoryStream]::new()
Get-ChildItem 'external/lean.tar.gz.a?' | Sort-Object Name | ForEach-Object {
  $b = [IO.File]::ReadAllBytes($_.FullName); $ms.Write($b, 0, $b.Length)
}
[IO.File]::WriteAllBytes("$PWD/external/lean.tar.gz", $ms.ToArray())
Remove-Item 'external/lean.tar.gz.a?'

# 1C. Same Python hash check as above
python -c "import hashlib,pathlib;p=pathlib.Path('external/lean.tar.gz');print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

</details>

### Step 2: Verify the MIT Challenge Export & Decode Theorem ASTs / 第二步：核验 MIT 挑战导出并反解定理语法树

 Even without downloading `lean.tar.gz`, `challenge_check.py` automatically downloads `challenge.ndjson.zst` from MIT if missing, decompresses it to `external/challenge.ndjson` (350,862,311 bytes), and verifies all hashes and declaration counts:

```bash
# 2A. Verify two-tier SHA-256 (zst + ndjson) and 51,692 declaration lines
python challenge_check.py
# Expected output:
#   zst size=46881299 sha256=c24ef99dab3556a52c7fb886e03cf22a242f3b96f82ae4cc40539e5d2f678ac6 ... MATCH=True
#   ndjson size=350862311 sha256=bd484ac9886a96f26b1d9a7a59ebd45b7a70d102c015d4f31f9302bbdd6ab2b9 ... MATCH=True
#   lines=51692 expected=51692 MATCH=True

# 2B. Confirm the 5 target theorems in challenge.ndjson are pure statement specs (sorryAx placeholders)
#     and the environment declares only 4 axioms (propext, Quot.sound, Classical.choice, sorryAx)
python sorry_check.py

# 2C. Reconstruct human-readable Lean 4 type signatures for the 5 theorems & 4 Props from the NDJSON DAG
python decode_challenge.py
```

### Step 3: Stream-Audit the 175,187-File Corpus & Import DAG / 第三步：流式扫描 17.5 万源码文件与依赖 DAG

`eng_stats.py` streams directly from `external/lean.tar.gz` (or `.zip` / extracted directory) in memory without unpacking 175,187 tiny files onto your filesystem:

```bash
# Scan all 175,187 .lean files directly from external/lean.tar.gz
python eng_stats.py --archive external/lean.tar.gz

# Outputs written to:
#   analysis/eng_stats.json  (structured metrics: LOC distribution, 12 libraries, 753,569 DAG edges, top hubs)
#   analysis/eng_stats.txt   (176-line human-readable engineering report)
```

---

## 4. Panoramic Dependency Structure (175,187 Files) / 17.5 万文件全景依赖结构摘要

### 4.1 The 12 Top-Level Lean Libraries (`lakefile.toml`) / 十二个顶层库分布

The project is organized into 12 Lean libraries totaling **175,187** files and **17,374,215** lines of code. Every single file (100.0%) lies in the transitive import closure of `src/Main.lean`. The module import graph forms a strict **DAG with 0 cycles**, **753,569** intra-project directed edges, median depth **68**, 90th-percentile depth **124**, and maximum depth **202**.

全库在 `lakefile.toml` 中划分为 12 个顶层库，共计 **175,187** 个 `.lean` 文件、**17,374,215** 行代码。从 `src/Main.lean` 出发的 import 闭包覆盖全部 **175,187** 个文件（可达率 100.0%），构成一张 **0 环**、**753,569** 条工程内部有向边、最大深度 **202**（中位深度 68，P90 深度 124）的有向无环图（DAG）。

```text
                       ┌────────────────────────────────────┐
                       │  src/Main.lean (5 Target Theorems) │
                       │  src/Statements.lean (4 Prop Defs) │
                       └─────────────────┬──────────────────┘
                                         │
                       ┌─────────────────▼──────────────────┐
                       │     Supplements (3 files, 22 L)    │
                       │  Kernels/MainTheorems: allChi,     │
                       │  rhOfAll, critAll, claimAll        │
                       └────────┬──────────────────┬────────┘
                                │                  │
        ┌───────────────────────▼──────┐    ┌──────▼───────────────────────┐
        │  Development (141,928 files) │    │   Formalism (18,254 files)   │
        │  12,232,663 lines (81.0%)    │◄──►│   3,200,748 lines (10.4%)    │
        │  • AbelianVariety  (99,187)  │    │   • SharpRestriction (Zero)  │
        │  • AutomorphicArith(18,431)  │    │   • GammaFactorNonvanishing  │
        │  • AutomorphicSpec (15,147)  │    │   • HermitianCurvature       │
        │  • WeilBound        (7,051)  │    └──────────────┬───────────────┘
        │  • EtaleCohomology  (1,398)  │                   │
        │  • ResolutionSing     (499)  │                   │
        │  • DiscreteGroups     (215)  │                   │
        └──────────────┬───────────────┘                   │
                       │                                   │
        ┌──────────────▼───────────────────────────────────▼───────────────┐
        │  Foundation & Bridge Libraries (14,995 files, 1,940,734 lines)   │
        │  • GroundTheory & GroundTheoryFields (8,507 files, 1,119,138 L)  │
        │  • ReciprocityTheory                 (3,845 files,   563,016 L)  │
        │  • CompanionTheory                   (2,027 files,   194,218 L)  │
        │  • PositivityTheory                    (449 files,    55,130 L)  │
        │  • Lemmata (167 files, 9,232 L)  • BuildAid (5 files, 20 L)      │
        └──────────────────────────────────────────────────────────────────┘
```

| Library / 顶层库 | Files / 文件数 | Share / 占比 | Lines / 代码行数 | Primary Mathematical Role / 核心数学职责 |
| :--- | ---: | ---: | ---: | :--- |
| **`Development`** | 141,928 | 81.01% | 12,232,663 | Main mathematical engine: `AbelianVarietyTheory` (99,187), `AutomorphicArithmetic` (18,431), `AutomorphicSpectrum` (15,147), `WeilBound` (7,051), `EtaleCohomology` (1,398), `ResolutionOfSingularities` (499), `DiscreteGroups` (215) |
| **`Formalism`** | 18,254 | 10.42% | 3,200,748 | Analytic & spectral infrastructure: `SharpRestriction` (`ZeroFreeAll`), `GammaFactorNonvanishing` (`VW` functional-equation reflection), `HermitianCurvature` |
| **`GroundTheory`** (+ `Fields`) | 8,507 | 4.86% | 1,119,138 | Algebraic/arithmetic ground structures, local-global fields, adeles, valuation rings |
| **`ReciprocityTheory`** | 3,845 | 2.19% | 563,016 | Shimura varieties, toroidal compactification (`UniformisationConclusion`), reciprocity laws |
| **`CompanionTheory`** | 2,027 | 1.16% | 194,218 | Companion representations, weight filtration, cohomological bridges |
| **`PositivityTheory`** | 449 | 0.26% | 55,130 | Positivity, Arakelov intersection bounds, Hermitian metric inequalities |
| **`Lemmata`** | 167 | 0.10% | 9,232 | Shared foundational algebraic and analytic lemmas |
| **`BuildAid`** | 5 | <0.01% | 20 | `D1.lean`–`D5.lean`: `LibrarySuggestions.nameDenyListExt` build acceleration |
| **`Supplements`** | 3 | <0.01% | 22 | `Kernels/MainTheorems.lean`: packages `allChi`, `rhOfAll`, `critAll`, `claimAll` |
| **`Main` + `Statements`** | 2 | <0.01% | 28 | Public specification (`Statements.lean`, 16 L) and final theorem bindings (`Main.lean`, 12 L) |
| **Total / 合计** | **175,187** | **100.00%** | **17,374,215** | **1,030,531,854 bytes (~1.03 GB raw source); 241,106 `theorem` declarations** |

### 4.2 High-Granularity Micro-File Architecture / 微文件与声明-证明分离架构

Statistical scan (`eng_stats.py`) reveals how an AI-authored 17.37-million-line formalization avoids context-window blowup and elaborator timeouts:
- **Ultra-fine file granularity**: Median file length is **30 lines** (mean **99.2 lines**, P90 **229 lines**, P99 **763 lines**). **61.8%** of all files (`108,334` files) contain **exactly 1 `theorem`**.
- **Statement / Proof decoupling**: **45,519** files end with `*Statement.lean` (median length **7 lines**), paired with sibling proof files in the same directory (**89.3%** exact same-directory pairing) or `Proofs/` subdirectories (**44,413** files).
- **Adapter wrappers (`first | exact @…`)**: **39,011** files act as signature-alignment wrappers using `by first | exact @…`, bridging module namespaces without re-elaborating heavy proof terms.
- **Top 5 Global Fan-In Hubs** (most imported modules across the entire DAG):
  1. `Development.AbelianVarietyTheory.Definitions.Divisors.CTSmallCone` (**3,088** direct importers)
  2. `Development.AbelianVarietyTheory.PublishedTheorems.ThetaCorrespondence.SiegelWeilAnisotropicHermitian` (**2,972** importers)
  3. `Development.AbelianVarietyTheory.PublishedTheorems.AutomorphicForms.DiscreteSeriesHermitianUnique` (**2,518** importers)
  4. `Development.AbelianVarietyTheory.PublishedTheorems.AutomorphicForms₂.ExistsNormLeHeightPow` (**2,460** importers)
  5. `ReciprocityTheory.PublishedTheorems.ToroidalCompactification.UniformisationConclusion` (**2,390** importers)

---

## 5. Core Code Anchor Quick-Reference / 核心代码锚点速查表

Every path below is relative to the extracted root of `lean.tar.gz` and has been line-verified against the source archive (`SHA-256: 9631b4f0…`). Effectively tracing the proof from `src/Main.lean` down to the analytic and arithmetic roots requires following a **13-hop backbone chain**.

下表列出从 `src/Main.lean` 顶层定理一路下钻到解析核心（Landau 实轴邻域非零）与算术深根（Galois 表示几何实现与局部 Langlands 对应）的精确文件与行号锚点。所有路径与行号均已在官方源码归档（`9631b4f0…`）中逐一核对。

### 5.1 The 13-Hop Proof Backbone (Top-Down) / 主证明链核心锚点（自顶向下）

| Hop / 层级 | File Path (relative to `lean.tar.gz` root) & Line / 源码路径与行号 | Key Symbol / 核心标识符 | Mathematical & Structural Role / 在证明链中的作用 |
| :-: | :--- | :--- | :--- |
| **01** | `src/Main.lean:4-12`<br>`src/Statements.lean:3-16` | `riemannHypothesis`<br>`LFunction_ne_zero_of_half_lt_re` | Top-level entry point: binds the 5 RH/GRH theorems to `rhOfAll`, `allChi`, `claimAll.2.1`, `critAll`. |
| **02** | `src/Supplements/Kernels/MainTheorems.lean:5-11` | `allChi`, `rhOfAll`, `critAll`, `claimAll` | Top-level kernel adapter: unpacks `UpperTheory.Claim.all_claims` from `EveryCharacter`. |
| **03** | `src/Development/AutomorphicArithmetic/CharacterBoxes/ClaimStrip.lean:40-98`<br>`…/CharacterBoxes/RiemannHypothesisOfEveryCharacter.lean:224`<br>`src/Formalism/GammaFactorNonvanishing/CritLine.lean:7,11,29`<br>`src/Formalism/GammaFactorNonvanishing/RhOfRight.lean:5` | `Claim.strip`, `Claim.zeta`<br>`VW.gammaFactor_ne_zero`<br>`VW.critLine`, `VW.rh_of_right` | **Half-plane to critical line reflection**: uses Euler product factor nonvanishing, $\Gamma$-factor nonvanishing, and the completed L-function functional equation for primitive characters to deduce RH & GRH from $\operatorname{Re}(s) > 1/2$ nonvanishing (`EveryCharacter`). |
| **04** | `src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean:7,10` | `everyCharacter_of_row`<br>`FinalTheorems.everyCharacter` | Combines `everyCharacter_of_row` with deep root `galoisLocalGlobalStrong_recParameter` (`RowSrc.lean:6`). *(Note: `:13` `FinalTheorems.riemannHypothesis` is unreferenced dead code; `Main.lean` goes via `Supplements`)*. |
| **05** | `src/Development/AutomorphicArithmetic/AutomorphicVarieties/ModularityArgument/ThresholdArguments/DenseThresholdCases/VwinOfRow.lean:4-5` | `One.vwin_of_row` | Deduces the window condition `UpperTheory.Top.VWin` (`∀ ψ, VWinAt ψ 401`, `ExistsPageN.lean:49`) from the Galois representation existence statement `Row0b`. |
| **06** | `src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/EveryCharacterOfLiteratureOfVWin.lean:215,810-814` | `OpenLiteratureStatements`<br>`every_character_of_literature_of_vWin` | Packages 3 structural inputs (`Row0b`, `RecTExists`, `Row0b`) into `OpenLiteratureStatements` (`:215`) and instantiates them at `:813` via `⟨h, UpperTheory.Zero.LLC.recTExists, h⟩` (0 axioms, all proved theorems). |
| **07** | `src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/SiegelEisensteinSecondTermHypotheses.lean:44,69-73` | `nonempty_hyps_definite_side_of_closed_bound`<br>`every_character_of_theta_integrals_local_matching` | Constructs the 46-field `HypsAlt` hypothesis witness from closed height/Arakelov bounds (`Outright.lean:13` `hsUse_outright`) and feeds it to the theta-integral local matching theorem. |
| **08** | `src/Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/TopPlug.lean:12,16-18` | `zero_free_all_of_green_v_win`<br>`every_character_of_green_v_win` | Combines the Green character labeling (`green_of_regular P.greenRegularCharacters`, `LabelDatum.lean:108`) with `VWin` to establish `ZeroFreeAll`. |
| **09** | `src/Development/AutomorphicArithmetic/CharacterBoxes/ZeroFreeAllOfTopG.lean:12,26`<br>`…/CharacterBoxes/Imprimitive.lean:5-7` | `TopG`, `zeroFreeAll_of_topG`<br>`Top.imprimitive` | Converts the family connectivity condition `TopG` into `ZeroFreeAll`, then lifts primitive-character nonvanishing (`PChar`) to arbitrary Dirichlet characters (`Top.imprimitive : ZeroFreeAll → EveryCharacter`). |
| **10** | `src/Formalism/SharpRestriction/RamificationFrobenius/TotientGaloisClasses/ExplicitFormulaErrorOfHostConditions.lean:14,18` | `ZeroFreeOn`<br>`ZeroFreeAll` | Defines `ZeroFreeAll := ZeroFreeOn (fun _ => True)` where `ZeroFreeOn Q := ∀ ψ : PChar, Q ψ → ψ.ZeroFreeAbove (1/2)`, connecting explicit-formula error bounds to zero-freeness. |
| **11** | `src/Development/AutomorphicArithmetic/PrimitiveCosets/Imports.lean:8`<br>`src/Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/ZeroFreeOfRpowWindow.lean:11,13` | `Comparison₂.formB`<br>`Deduction.zeroFree_of_rpow_window`<br>`Deduction.lemmaL` | **Unique Analytic Core on the Active Proof Chain**: converts power-window exponential/explicit-formula estimates (`FormB`) into $\operatorname{Re}(s) > 1/2$ zero-freeness via Landau's positivity argument (`lemmaL`). *(Note: `Formalism/.../Landau.lean:380` `landau_family` is an unreferenced parallel branch)*. |
| **12** | `src/Development/AutomorphicArithmetic/Foundations/GaloisRepresentations/IntegralStructures/RowSrc.lean:6`<br>`…/GaloisRepresentationsOfThetaLift.lean:6`<br>`…/GeometricFlagBases/WeightOneGeometricRealization.lean:11`<br>`…/ThetaParseval/ThetaKernels/TLiftK.lean:4` | `galoisLocalGlobalStrong_recParameter`<br>`galoisRepresentations_of_thetaLift`<br>`geoOne_holds`<br>`UpperTheory.TP.K.tLiftK` | **Arithmetic Deep Root A (`Row0b`)**: proves existence of $\ell$-adic Galois representations for regular algebraic polarized cuspidal automorphic representations over CM fields (`WeightsConjBis.lean:69`) from weight-one geometric realization (`geoOne_holds`) and $\theta$-lifting (`tLiftK`). |
| **13** | `src/Development/AutomorphicArithmetic/Foundations/LocalLanglands/LocalCentralUnits/RecTExists.lean:20,66,77` | `UpperTheory.Zero.LLC.recTExists`<br>`IsRecT`, `LawsT` | **Arithmetic Deep Root B (`RecTExists`)**: proves existence of the local Langlands correspondence parameter satisfying the 12 `LawsT` conditions (`artEx`, `exists_isLExt`). |

---

## 6. Repository Contents & Audit Perspective / 仓库文件清单与审计方法论

### 6.1 Tracked Files in This Repository / 本仓库文件清单

| File / 文件名 | Size / 大小 | Description / 说明 |
| :--- | ---: | :--- |
| [`00-总报告-我们做了什么.md`](00-总报告-我们做了什么.md) | 31.1 KB | Process log: task evolution phase by phase, layered evidence, what the audit cannot claim, and the corrections made along the way |
| [`README.md`](README.md) | 35.5 KB | Bilingual root guide: verification scorecard, 5 theorems, 3-step reproduction, 175k-file DAG summary, 13-hop code anchors |
| [`01-验证报告-黎曼猜想.md`](01-验证报告-黎曼猜想.md) | 27.2 KB | Full verification report: source identity, statement fidelity, axiom hygiene, static bypass scan, MIT & Hertaspace status timeline |
| [`02-中文导读与代码地图.md`](02-中文导读与代码地图.md) | 77.1 KB | Comprehensive Chinese reader's guide: LaTeX translations of the 5 theorems, 13-hop backbone walkthrough, 20-step `remark.pdf` anchor mapping, glossary |
| [`03-核心13跳-人类可读数学证明.md`](03-核心13跳-人类可读数学证明.md) | 34.8 KB | Human-readable proof of the 13-hop backbone in plain LaTeX: five theorems restated, Landau window criterion, interface-level account of the deep roots |
| [`04-AI千万行代码工程架构分析.md`](04-AI千万行代码工程架构分析.md) | 32.0 KB | Static engineering analysis of the corpus: 12-library split, file-size and LOC percentiles, Statement/Proof pairing, 753k-edge import DAG, limits of the template hypothesis |
| [`哈希清单-SHA256.txt`](哈希清单-SHA256.txt) | 4.6 KB | SHA-256 digests: the two official artifacts this repo does not ship (`lean.tar.gz`, `challenge.ndjson.zst`) plus every file in this repository |
| [`challenge_check.py`](challenge_check.py) | 6.7 KB | Cross-platform verifier for `challenge.ndjson.zst` and `challenge.ndjson` (SHA-256, byte size, 51,692 declaration lines) |
| [`sorry_check.py`](sorry_check.py) | 5.7 KB | AST scanner confirming the 5 target theorems in `challenge.ndjson` use `sorryAx` placeholders and only 4 axioms exist in the challenge |
| [`decode_challenge.py`](decode_challenge.py) | 9.8 KB | Standalone `lean4export` NDJSON DAG decoder that reconstructs the type expressions of the 5 target theorems and 4 custom `Prop`s |
| [`eng_stats.py`](eng_stats.py) | 39.8 KB | Streaming corpus analyzer for `lean.tar.gz` / `.zip` / directory: computes LOC percentiles, 12-library breakdown, 753,569-edge import DAG, and template skeletons |
| [`LICENSE`](LICENSE) | 1.1 KB | MIT license for all Python scripts and configuration files |
| [`LICENSE-docs`](LICENSE-docs) | 1.0 KB | CC BY 4.0 notice for the Chinese documents; states which upstream files are not covered |
| [`.gitignore`](.gitignore) | 285 B | Keeps `external/`, `analysis/`, `__pycache__` and downloaded archives out of Git |
| [`.gitattributes`](.gitattributes) | 171 B | Forces LF line endings for text files so hashes are stable across platforms |

### 6.2 Audit Perspective: Separating Formal Truth from Mathematical Understanding / 审计视角：形式核验与数学理解的边界

Auditing a 17.37-million-line machine-generated proof requires strict separation between **formal validity** and **human mathematical comprehension**:

1. **Why lightweight statement-export auditing matters**: Re-compiling 175,187 Lean files takes ~7 hours and 210 GiB of RAM. However, Lean's verification architecture separates *elaboration* from *kernel checking*. By auditing the 45 MB `challenge.ndjson.zst` statement export locally (via `challenge_check.py`, `sorry_check.py`, and `decode_challenge.py`) and pairing it with MIT's independent kernel logs (`nanoda` and `con-leche --compare`), any developer on an ordinary laptop can verify that the exact Mathlib statement of `RiemannHypothesis` was proved using only `[propext, Classical.choice, Quot.sound]`, with zero definition tampering.
2. **How AI engineered 175,187 files without collapsing under context limits**: Our full-corpus scan (`eng_stats.py`) shows that the codebase operates as a massively parallel assembly graph. With a median file length of 30 lines, 45,519 `*Statement.lean` interface files (median 7 lines), and 39,011 `first | exact @…` adapter modules, complex proof obligations are continuously sliced into isolated single-theorem compilation units.
3. **Beware of "Look-Alike" Dead Branches**: In a corpus of 175,187 files, grep-based exploration easily hits unreferenced parallel branches. For instance, `src/Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean:13` defines `FinalTheorems.riemannHypothesis`, and `src/Formalism/SharpRestriction/RamificationFrobenius/TotientGaloisClasses/Landau.lean:380` proves `landau_family`, yet import-graph closure proves that `src/Main.lean` uses neither: the actual active proof chain runs through `Supplements/Kernels/MainTheorems.lean` and `DedekindLFunctions/LandauTheorems/ZeroFreeOfRpowWindow.lean:11` (`Deduction.zeroFree_of_rpow_window`). Every anchor in Section 5 has been verified to lie on the active dependency chain from `src/Main.lean`.

### 6.3 What This Audit Does Not Claim / 本审计不主张什么

An audit is only useful when its boundaries are stated as plainly as its conclusions. Three things are deliberately left open here:

1. **No substitute for peer review.** Kernel acceptance certifies that the formal proof is well formed and follows from the stated axioms; it says nothing about whether the underlying human-level argument is new, correctly aimed, or publishable. Mathematical peer review of the human proof is still pending.
2. **No claim of a fully closed third-party loop.** When this repository was assembled, two MIT replay jobs (default and paranoid kernel, single-threaded over `solution.ndjson.zst`) and the end-to-end `lake comparator` run were still executing, and the Hertaspace build had reached 55.8% of its 183,903 tasks. Section 1 marks these ⏳ rather than ✅.
3. **No redistribution.** The official archive, the MIT exports, and the GitHub source zip stay on their publishers' servers. This repository ships hashes, scripts, and prose; `external/` is git-ignored and filled by your own download.

中文要点：内核接受只说明「形式证明在给定公理下成立」，不等于「数学证明已通过同行评审」；写这份仓库时两个 MIT 重放任务与 `lake comparator` 仍在运行；官方大文件一律不随仓库分发，`external/` 由使用者自行下载填充。

### 6.4 License / 许可

- **Code** (`*.py`, `LICENSE`, config files): MIT — see [`LICENSE`](LICENSE).
- **Documents** (`README.md`, `01`–`04`): CC BY 4.0 — see [`LICENSE-docs`](LICENSE-docs). Attribution: a link back to this repository is enough.

Hashes, file paths, and identifier names quoted in these documents describe public artifacts and are reproduced for verification.

### 6.5 Scope, Contact, and Corrections / 范围、联系与更正

This is a personal, independent audit. It is not affiliated with Levent Alpöge, Anthropic, or the MIT team, and carries no endorsement from them.

If you find an error — a wrong hash, a misquoted theorem signature, a stale status line — open an issue with the conflicting evidence. Corrections are applied to the documents and to [`哈希清单-SHA256.txt`](哈希清单-SHA256.txt) in the same commit, so the prose and the digests never drift apart. For questions about the formalization itself, the authoritative sources are <https://alpo.ge/> and <https://math.mit.edu/~drew/grh/>.

本仓库是个人独立核查，与作者、Anthropic、MIT 团队无隶属关系，也未获其背书。发现错漏请带证据开 issue；更正会同时更新文档与哈希清单，保证两者不脱节。
