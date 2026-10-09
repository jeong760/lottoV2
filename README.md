```markdown
# 🎰 Lotto 6/45 Analysis & Live Venus Turbine Dashboard

An advanced, real-time interactive Lotto 6/45 analysis dashboard featuring live Venus drum turbine simulations, multi-algorithm ensemble generation, 
continuous background AI training telemetry, and comprehensive statistical tracking.

---

## 🚀 Key Features

### 1. Live Venus Turbine & Ball Mixing Simulation

* **Real-time 300s Countdown & RPM Telemetry**: 
  Simulates the official Venus lotto drawing machine. 
  During the 300-second mixing countdown, the AI engine performs rigorous quality gate filtering and verifies combination validity.

* **Progressive Ball Extraction**: 
  Sequentially extracts 6 main balls and 1 bonus ball at 10-second intervals per set, rendering physics-based drum movements and animations.

* **Dynamic Algorithm Pool**: 
  Automatically or manually selects from 6 core professional algorithm groups for each draw sequence.

### 2. 6-Group Core Professional Algorithm Pool

* **Statistical Distribution Model**: Evaluates historical frequency and standard deviation balances.
* **Frequency Matrix Analyzer**: Maps hot/cold numbers through multi-dimensional matrix weights.
* **Machine Learning Gradient Engine**: Optimizes selection criteria using gradient descent scoring.
* **AI Neural Predictor**: Leverages continuous background auto-trained neural networks.
* **Historical Pattern Matcher**: Cross-references winning patterns across all official draws (#1 to latest).
* **Advanced Markov Chain Ensemble**: Calculates transition probability matrices for consecutive draws.

### 3. Comprehensive Analytics & Dashboards

* **Number Frequency Heatmap**: Visualizes frequency counts across all 45 numbers with custom color gradients and sorting options.
* **Ratio & Statistical Metrics**: Tracks Odd/Even, High/Low, AC Complexity, and SUM totals strictly from generated history.
* **Decade & Consecutive Distribution**: Analysis across 1-10, 11-20, 21-30, 31-40, and 41-45 ranges.
* **Official Draw History Viewer**: Complete database tracker of official historical draws with full 1st~5th prize details, total sales, and individual winner payouts.
* **Generated Sets Management**: View, batch-select, and export generated number sets to Excel (`.xlsx`) securely without table cell modification risks.

## ✅ Release Readiness Update (Phase C → K)

Recent phases focused on analytics expansion, explainability, and reliability hardening:

* **Expanded analytics surface**: Comprehensive Phase C statistical outputs, plus dedicated **Real-Time Analytics** and **Algorithm Backtesting** tabs.
* **Batch-aware history continuity**: `generation_batch_id` propagation/persistence with same-batch filtering and session drill-down in **Generated Sets**.
* **Explainability exports**: Session **Top-50** export and **Batch Report** export using shared reporting helpers.
* **Backtesting clarity**: Metrics now include hit/match rates and precision/recall/F1 definitions with average prediction coverage.
* **Legacy compatibility & resilience**: History loading now backfills legacy batch IDs and recovers from malformed numeric history rows.

---

## ✨ Bonus Swap Optimizer

The newly implemented **Bonus Swap Optimizer** is an advanced feature that elevates the fun and depth of lotto number simulation and analysis. 

Here is a summary of how it works and its core details:

### 1. Concept & Background

When analyzing or simulating Lotto 6/45, users often wonder: *"What if I had replaced one of my generated numbers with the bonus number? Would my prize rank have improved?"* 

This feature is designed to instantly simulate and answer such questions through mathematical and probabilistic evaluation.

### 2. Key Features & How It Works

* **Target Selection & Analysis**: 
  Select the number set you want to analyze from the **Generated Sets** view on the dashboard and click the `✨ Bonus Swap Optimizer` button.

* **Exhaustive 1-Number Swap Simulation**: 
  Automatically iterates through all 6 possible combinations by sequentially removing one of the 6 main numbers and replacing it with the corresponding draw's bonus number.

* **Official Draw Comparison**: 
  Evaluates each swapped combination against actual official winning numbers to determine match counts (`Matches`) and prize ranks (ranging from 1st to 5th place or miss).

* **Comprehensive Result Dialog (`BonusSwapDialog`)**: 
  Presents all simulation outcomes via a clean, structured dialog window, allowing users to see at a glance which number to discard and replace with the bonus number for the most advantageous outcome.

### 3. Expected Benefits

* **Strategic Insights**: 
  Empowers users to intuitively understand how critical the bonus number is in determining prize tiers (especially for the 2nd prize).

* **Enhanced Simulation Immersion**: 
  Moves beyond static number generation by enabling users to directly test scenarios that maximize winning potential through bonus number integration.

---

## 🔍 Quality Gate Filtering Rules & Clarification Note

### 1. Filtering Criteria (Number Generation Conditions)

During number generation and verification, combinations undergo strict quality checks. 

Sub-optimal or non-compliant candidates are automatically discarded, and new valid combinations are generated:

* **Odd / Even Ratio**: Evaluates the balance of odd and even numbers within the 6 selected numbers to filter out extreme skews (e.g., all odds or all evens).
* **High / Low Ratio**: Validates the distribution balance between low numbers (1-22) and high numbers (23-45) based on median values.
* **AC Complexity (Arithmetic Complexity)**: Measures randomness and structural complexity based on the count of unique absolute differences between pairs of numbers, filtering out overly regular patterns.
* **SUM Total Range**: Ensures that the sum of the 6 numbers falls within statistically probable winning ranges.
* **Decade Distribution**: Analyzes distribution across ranges to prevent clumping in a single decade.
* **Consecutive Numbers Restriction**: Filters out excessive or completely absent consecutive sequences to mirror historical winning patterns.

---

## 📐 Understanding Match Counts (0, 1, or 2 Matches in Generated Sets)

In the **Generated Sets** table, observing **0, 1, or 2 matches** is not an error; it is a **statistically normal and natural phenomenon**. 

Here is why:

### 1. The Exact Meaning of "Matches"

* The **Matches** and **Rank** metrics displayed in the table indicate how many numbers overlap when comparing your generated set against actual official winning numbers (e.g., the most recent official draw).
* The probability of matching all 6 numbers to win the 1st prize in Lotto 6/45 is approximately **1 in 8.14 million**. 
  Therefore, when compared against actual winning draws, having **0, 1, or 2 numbers match** is statistically the most natural and frequent result for any number combination.

### 2. The True Role of Quality Gate Filters

* The program’s algorithms and statistical filters act as validation mechanisms to check whether a combination **"possesses natural statistical characteristics similar to actual lotto winning numbers."**
* For instance, they screen out unrealistic or extreme human-biased patterns (such as `1, 2, 3, 4, 5, 6`) to yield realistic combinations.
* In short, filters are designed to **exclude unreasonable or irrational combinations**, not to function as an "oracle device that accurately predicts future winning numbers."

### Summary

Regardless of how powerful an AI or statistical model is used, due to the inherent randomness of lotto draws, comparing generated sets against past winning draws will naturally result in **0 to 2 matches**. 

Since the filters are operating correctly, you can enjoy the simulation with complete peace of mind!

---

## ⚙️ Detailed Component Roles & Architecture

### ① AI & Deep Learning Core (`core/ai_learning_model.py` & `core/engines/ai_engine.py`)

* **Multi-Model Ensemble**: Leverages TensorFlow/Keras-based **LSTM (Long Short-Term Memory)** and **GRU (Gated Recurrent Unit)** recurrent neural networks to learn sequence patterns across draws.
* **ARIMA Time Series Analysis**: Utilizes `statsmodels` to predict short-term emergence momentum and moving average trends for individual numbers.
* **Markov Transition Probability & Co-occurrence**: Computes transition probability matrices indicating how a preceding draw influences the next, alongside frequently co-occurring number pairs.
* **Statistical Constraint Filtering (10 Core Rules)**: Strictly filters combinations based on optimal sum ranges (100–170), odd/even and high/low balance, AC value (arithmetic complexity), trailing digit variance, and sector dispersion.

### ② Advanced Statistics Engine (`core/engines/statistics_engine.py`)

* **Periodicity & Gap Analysis**: Evaluates missing duration and standard deviation of appearance intervals for each number to identify **Hot/Cold numbers**.
* **Chi-Square Goodness-of-Fit Test (`scipy.stats.chisquare`)**: Verifies statistical significance ($p$-value) against a purely random uniform distribution across historical winning numbers, diagnosing bias states (`Undersampled`, `Oversampled`, `Balanced`).

### ③ Data & Persistence Layer (`data/`)

* **LottoDBHelper & LottoRepository**: Securely queries and parses raw lotto winning histories, absorbing structural differences between legacy and modern data formats.
* **MLModelRepository**: Safely persists AI model training states and weights as JSON and SQLite binary blobs (`ml_weights` table in `mllearn.db`).

### ④ Asynchronous Background Worker (`workers/ai_train_worker.py`)

* Inherits from PyQt `QThread` to perform periodic background AI auto-training without causing UI freezing.
* Transmits training progress metrics (epochs, loss, accuracy) in real-time via `progress_signal` to seamlessly update the UI progress bar.

---

## 🚀 Program Workflow Summary

1. **Application Launch (`launcher.py` ➔ `MainWindow`)**: When executing the program, lazy loading via `core/__init__.py` and `core/engines/__init__.py` ensures modules are safely loaded without circular reference issues.
2. **Background Training (`AITrainWorker`)**: A dedicated background thread initializes, fetches historical winning records from the database, and executes deep learning training and statistical matrix extraction via `LottoAILearningModel`.
3. **Result Persistence & Utilization**: Trained weights and states are serialized and stored in `mllearn.db`. When the user requests optimal combination generation, the system passes candidates through 10 statistical filters to deliver high-probability lotto number sets.

---

## ⚙️ Prerequisites & Quick Start

### Prerequisites

* Python 3.14+
* PyQt5, Pandas, OpenPyXL, Psutil

### Installation & Execution

```bash
# 1. Clone the repository
git clone [https://github.com/your-username/lotto-project.git](https://github.com/your-username/lotto-project.git)
cd lotto_project

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python launcher.py

```

---

## 🔄 Application Booting & Execution Pipeline

The execution sequence outlines the entire lifecycle of LottoMaster Pro, starting from launching the application to reaching a fully interactive dashboard state:

```text
[User] Execute launcher.py (python launcher.py)
  │
  ├── 1. Setup Logging & Environment Path
  │     ├── Safely inject project root directory into sys.path
  │     ├── Initialize centralized logger and file handlers (FlushingFileHandler)
  │     └── Verify and create local log directories and log files
  │
  ├── 2. Dependency & Module Validation
  │     ├── Check availability of core libraries (PyQt5, psutil, pandas, tensorflow, etc.)
  │     └── Catch and log critical exceptions if essential packages are missing
  │
  ├── 3. QApplication Initialization
  │     ├── Compute available screen geometry coordinates
  │     └── Configure high-resolution and window scaling properties
  │
  ├── 4. Main Window Instantiation (LottoMainWindow.__init__)
  │     ├── [Algorithm Hub] Dynamically load core.algorithm_hub and instantiate AI engine
  │     ├── [State Variables] Initialize runtime state variables (live_sets, current_set_index, drawing_phase, etc.)
  │     ├── [Timers] Configure and start turbine timers, physics engine timers (13ms), and AI training timers (30 min)
  │     └── [UI Layout Engine] Execute init_ui() to assemble the complete dashboard structure
  │
  ├── 5. Asynchronous Background Initialization & Synchronization (SingleShot QTimers)
  │     ├── [400ms] init_auto_data_update(): Fetch official lotto results and synchronize widget statistics
  │     ├── [700ms] _update_metrics_from_generated_history(): Load stored generation history to refresh metrics
  │     └── [1000ms] init_auto_ai_training(): Launch background AI 50-epoch auto-training worker (AITrainWorker)
  │
  └── 6. Dashboard Rendering & Event Loop Entry (sys.exec_())
        └── Render application window centered on screen and enter standby/ready state for user interaction

```

### 🪟 UI Layout Architecture (`init_ui` Hierarchy)

When `launcher.py` invokes `MainWindow`, the graphical interface is structured hierarchically as follows:

```text
[QMainWindow: Lotto 6/45 Analysis Dashboard]
  │
  └── [Central Widget] (Main Vertical Layout)
        │
        └── [QTabWidget] (8 Core Functional Tabs)
              │
              ├── Tab 1: [Live Venus Turbine Generator] (Main Drawing Dashboard)
              │     ├── [HeaderWidget] (Top title and system header)
              │     └── [QSplitter (Horizontal)] (Left-Right Split Layout)
              │           ├── [Left Container - Scroll Area] (Analytical & Metrics Area)
              │           │     ├── [Metrics Container] (Odd/Even, High/Low, AC, and SUM widgets)
              │           │     ├── [Decade & Consecutive Container] (Decade distribution & consecutive sequence widgets)
              │           │     └── [LottoHeatmapWidget] (Frequency counts and gap heatmap)
              │           │
              │           └── [Right Container] (Turbine & Control Area)
              │                 ├── [VenusDrumWidget] (Real-time Venus turbine drawing simulation)
              │                 ├── [DrawingStartStopWidget] (Start, stop, and skip control buttons)
              │                 ├── [SystemParametersWidget] (Algorithm selector, RPM, and mixing duration settings)
              │                 ├── [Ratio & Statistical Metrics] (Ratio balance and statistical metrics widgets)
              │                 └── [LiveConsoleWidget] (Real-time console telemetry & status panel)
              │
              ├── Tab 2: [Generated Sets] (Generated number sets management widget)
              ├── Tab 3: [Real-Time Analytics] (Live statistical and trend dashboard)
              ├── Tab 4: [Algorithm Backtesting] (Comparative algorithm vs random baseline evaluation)
              ├── Tab 5: [Machine Learning Performance] (Machine learning training status & performance widget)
              ├── Tab 6: [Official Draw History (#1~Latest)] (Historical official winning rounds viewer widget)
              ├── Tab 7: [Database Management] (DB maintenance and operational utilities)
              └── Tab 8: [System Parameters] (Runtime system and engine parameter controls)

```

### 📋 Booting Console Log Timeline Summary

During startup, the application outputs a sequential log timeline reflecting successful initialization stages:

1. **`[INFO] [LottoLauncher]: Initializing LottoMaster Pro Desktop Application...`** (Launcher startup)
2. **`[INFO] [LottoMainWindow]: Initializing automatic lotto data update and widget synchronization...`** (API fetch & state synchronization)
3. **`[INFO] [StatisticsWidgetConnector]: All analytical statistics successfully pushed to connected UI widgets...`** (Statistical engine data injection complete)
4. **`[INFO] [LottoMainWindow]: System Resource Status -> CPU: X% | RAM: Y%`** (System resource monitoring check)
5. **`[INFO] [LottoMainWindow]: AI Model: Running continuous background 50-epoch auto-training...`** (Background AI worker spawned)
6. **Dashboard UI fully activated (`QUALITY GATE STATUS: Standby`)** 🟢

---

## 🗄️ Database & Concurrency Architecture

### 1. Database & Caching (`lotto_history.db` / `lottomater.db`)

* **SQLite Local Storage**: Securely stores official draw records, prize details, and generated number sets (`Generated Sets`).
* **Automated Data Sync (`updater.py`)**: Automatically fetches and synchronizes official historical records upon startup, enabling fully offline analysis capability.

### 2. Background Concurrency & Performance Design

* **`QThread` Workers**: Offloads heavy computations and background model training (`LottoWorker` for number generation, `AITrainWorker` for 30-minute periodic AI weight updates) to prevent UI freezing.
* **`QTimer` Telemetry**: Drives 1-second interval mixing countdowns, system resource telemetry (`psutil`), and smooth real-time UI updates.

---

## 📊 Dashboard Widget Reference

| Widget Name | Module Path | Description |
| --- | --- | --- |
| **VenusDrumWidget** | `ui/widgets/venus_drum_widget.py` | Simulates official Venus lottery drum physics and RPM telemetry. |
| **LiveConsoleWidget** | `ui/widgets/live_console_widget.py` | Displays real-time quality gate status, resource monitoring, estimated time, and incremental filtered/discarded combination counts. |
| **GeneratedSetsWidget** | `ui/widgets/generated_sets_widget.py` | Manages generated sets history, rank comparison, secure Excel (`.xlsx`) exports, and **Bonus Swap Optimizer**. |
| **RealTimeAnalyticsWidget** | `ui/widgets/real_time_analytics_widget.py` | Displays live analytics snapshots (hot/cold, overdue, trend, and pattern summaries). |
| **BacktestWidget** | `ui/widgets/backtest_widget.py` | Runs algorithm backtests and exports standardized report output. |
| **LottoHeatmapWidget** | `ui/widgets/heatmap_widget.py` | Visualizes frequency heatmaps across all 45 numbers with custom color gradients. |

---

## 🛠️ Project Directory Structure

```text
lottoV2/
│
├── core/
│   ├── __init__.py                # Core package initialization with lazy loading
│   ├── algorithm_hub.py           # Central hub managing algorithm ensemble & scoring
│   └── engines/
│       ├── __init__.py            # Engine package with lazy export mechanism
│       ├── lotto_engine.py        # Core computational prediction engine
│       ├── real_ml_engine.py      # Machine learning inference engine
│       └── ml_engine_runner.py    # ML runner pipeline
│
├── data/
│   ├── lotto_db_helper.py         # SQLite database helper for generation history and batch/session metadata continuity
│   ├── updater.py                 # Automated updater fetching official draw records
│   └── repositories/
│       └── lotto_repository.py    # Data repository handling official draw queries
│
├── ui/
│   ├── main_window.py             # Main application window managing state, timers, & workers
│   └── widgets/                   # Modular dashboard UI widgets
│       ├── header_widget.py
│       ├── ml_status_widget.py
│       ├── official_draw_history_widget.py
│       ├── generated_sets_widget.py   # Includes BonusSwapDialog & optimization triggers
│       ├── real_time_analytics_widget.py
│       ├── backtest_widget.py
│       ├── db_management_widget.py
│       ├── heatmap_widget.py
│       ├── venus_drum_widget.py
│       ├── drawing_startstop_widget.py
│       ├── live_console_widget.py
│       ├── system_parameters_widget.py
│       ├── odd_even_widget.py
│       ├── high_low_widget.py
│       ├── ac_widget.py
│       ├── sum_widget.py
│       ├── ratio_balance_widget.py
│       ├── statistical_metrics_widget.py
│       ├── decade_dist_widget.py
│       └── consecutive_widget.py
│
├── workers/
│   ├── lotto_worker.py            # Asynchronous thread worker for number generation & filtering
│   └── ai_train_worker.py         # Background thread worker for continuous AI model training
│
├── launcher.py                    # Application launcher entry point
└── README.md                      # Project documentation

```

---

## 🔄 Number Generation & Drawing Workflow

```text
[1. User Action: Generation Trigger]
  └── User clicks "Generate" on DrawingStartStopWidget (`ui/widgets/drawing_startstop_widget.py`)
        │
        ▼
[2. Asynchronous Thread Dispatch]
  └── LottoMainWindow initializes LottoWorker (`workers/lotto_worker.py`) in a background QThread
        │   - Prevents UI freezing during heavy calculations
        │   - Interacts with AlgorithmHub (`core/algorithm_hub.py`)
        │
        ▼
[3. Algorithm Ensemble & Quality Filtering]
  └── Selected algorithm group generates raw number candidates
        │   - Filters out non-compliant combinations based on Quality Gate Rules
        │   - Computes discarded combinations count (Discarded Combinations)
        │
        ▼
[4. Live Venus Turbine Mixing Phase (300s Countdown & AI Quality Filtering)]
  └── LottoMainWindow triggers start_live_turbine() and starts turbine_timer (1s interval)
        │   - VenusDrumWidget simulates drum physics (RPM telemetry)
        │   - LiveConsoleWidget dynamically resets and incrementally accumulates/displays real-time filtered/discarded combinations 
        │     alongside quality gate status for each individual set mixing countdown
        │
        ▼
[5. Sequential Ball Extraction Sequence (10s Interval per Ball)]
  └── Once mixing countdown reaches 0, process_next_extraction_ball() begins
        │   - Extracts 6 main balls and 1 bonus ball sequentially at 10-second intervals with set progress (Set X/Y)
        │   - Renders ball objects dynamically onto the Venus drum tray
        │
        ▼
[6. Database Persistence & Real-Time Dashboard Sync]
  └── Upon completion of each set:
        │   - Securely saves generated set records to SQLite via LottoDBHelper (`core/lotto_db_helper.py`)
        │   - Automatically refreshes dependent widgets:
            ├── GeneratedSetsWidget (Updates table history, ranks, match counts, & Bonus Swap Optimizer access)
            ├── OfficialDrawHistoryWidget (Updates official draw records)
            ├── LottoHeatmapWidget (Updates number frequency heatmaps)
            └── Ratio & Statistical Metrics Widgets (Recalculates Odd/Even, High/Low, AC, and SUM totals)

```

---

## 🔮 Roadmap / Future Enhancements

* [ ] Integrate external deep learning frameworks (PyTorch/TensorFlow) options to further enhance machine learning predictive accuracy.
* [ ] Implement real-time multi-language UI switching (Korean/English).
* [ ] Enhance backtesting simulation capabilities for generated number sets.

---

## 💻 Tech Stack

* **Language**: Python 3.14+
* **GUI Framework**: PyQt5
* **System Monitoring**: Psutil
* **Data Processing & Export**: Pandas, OpenPyXL
* **Database**: SQLite (via custom helper & repository pattern)
* **Concurrency**: QThread, QTimer (Asynchronous workers preventing UI freeze)

```

```