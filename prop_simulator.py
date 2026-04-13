from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import numpy as np

Outcome = Literal["pass", "breach", "timeout"]
TraderStyle = Literal["Aggressive", "Balanced", "Conservative"]
StrategyMode = Literal["Mechanical", "Discretionary"]


@dataclass(frozen=True)
class StreakConfig:
    no_trade_prob: float = 0.22
    hot_start_prob: float = 0.04
    cold_start_prob: float = 0.08
    hot_shift: float = 0.18
    cold_shift: float = -0.22
    hot_continue_prob: float = 0.75
    cold_continue_prob: float = 0.83


@dataclass(frozen=True)
class SimulationConfig:
    profit_target: float = 3000.0
    dd_limit: float = 2000.0
    win_rate: float = 0.60
    profit_factor: float = 1.6
    strategy_mode: StrategyMode = "Mechanical"
    be_trade_percent: float = 0.0
    consistency_limit_percent: float = 0.0
    max_steps: int = 300
    num_sims: int = 3000
    trader_style: TraderStyle = "Balanced"
    risk_step: int = 25
    recommendation_num_sims: int = 2000
    streaks: StreakConfig = field(default_factory=StreakConfig)

    @property
    def avg_loss_r(self) -> float:
        return 1.0

    @property
    def avg_win_r(self) -> float:
        return self.profit_factor

    @property
    def consistency_cap_amount(self) -> Optional[float]:
        if self.consistency_limit_percent <= 0:
            return None
        return self.profit_target * (self.consistency_limit_percent / 100.0)


@dataclass(frozen=True)
class PathResult:
    equities: np.ndarray
    trailing_floors: np.ndarray
    outcome: Outcome
    steps_taken: int
    trades_executed: int
    final_equity: float
    peak_equity: float


@dataclass(frozen=True)
class SimulationSummary:
    risk_dollars: int
    dynamic: bool
    total_runs: int
    pass_count: int
    breach_count: int
    timeout_count: int
    pass_rate: float
    breach_rate: float
    timeout_rate: float
    avg_steps_to_pass: Optional[float]
    avg_trades_to_pass: Optional[float]
    avg_steps_all: float
    avg_trades_all: float


@dataclass(frozen=True)
class Recommendation:
    label: str
    risk_dollars: int
    dynamic: bool
    summary: SimulationSummary
    rationale: str


@dataclass(frozen=True)
class SimulationReport:
    fixed: Recommendation
    dynamic: Recommendation
    aggressive: Recommendation
    balanced: Recommendation
    conservative: Recommendation
    selected: Recommendation
    fastest_safe: Recommendation

    @property
    def matrix_rows(self) -> List[Dict[str, object]]:
        plans = [
            self.fixed,
            self.dynamic,
            self.aggressive,
            self.balanced,
            self.conservative,
            self.fastest_safe,
        ]
        rows: List[Dict[str, object]] = []
        for plan in plans:
            rows.append(
                {
                    "Plan": plan.label,
                    "Risk": f"${plan.risk_dollars}",
                    "Pass %": plan.summary.pass_rate,
                    "Breach %": plan.summary.breach_rate,
                    "Timeout %": plan.summary.timeout_rate,
                    "Avg Pass Steps": plan.summary.avg_steps_to_pass,
                    "Avg Pass Trades": plan.summary.avg_trades_to_pass,
                }
            )
        return rows


STYLE_RULES: Dict[TraderStyle, Dict[str, float]] = {
    "Aggressive": {
        "min_pass_rate": 50.0,
        "min_risk_fraction": 0.35,
        "max_risk_fraction": 0.60,
        "pass_weight": 1.0,
        "breach_weight": 1.0,
        "steps_weight": 2.5,
        "risk_weight": 0.08,
    },
    "Balanced": {
        "min_pass_rate": 75.0,
        "min_risk_fraction": 0.20,
        "max_risk_fraction": 0.35,
        "pass_weight": 2.0,
        "breach_weight": 3.0,
        "steps_weight": 1.0,
        "risk_weight": 0.0,
    },
    "Conservative": {
        "min_pass_rate": 90.0,
        "min_risk_fraction": 0.10,
        "max_risk_fraction": 0.20,
        "pass_weight": 3.0,
        "breach_weight": 5.0,
        "steps_weight": 0.25,
        "risk_weight": -0.05,
    },
}


STYLE_DESCRIPTIONS: Dict[TraderStyle, str] = {
    "Aggressive": "Prioritizes speed and accepts lower pass probability.",
    "Balanced": "Balances speed with account protection.",
    "Conservative": "Prioritizes survival and 90%+ pass probability when available.",
}


def calculate_expectancy(config: SimulationConfig) -> float:
    base_expectancy = (
        config.win_rate * config.avg_win_r
        - (1.0 - config.win_rate) * config.avg_loss_r
    )
    if config.strategy_mode == "Mechanical":
        return base_expectancy
    return (1.0 - config.be_trade_percent / 100.0) * base_expectancy


def _resolve_trade_outcome(
    config: SimulationConfig,
    rng: np.random.Generator,
    win_probability: float,
) -> float:
    if (
        config.strategy_mode == "Discretionary"
        and rng.random() < (config.be_trade_percent / 100.0)
    ):
        return 0.0
    return config.avg_win_r if rng.random() < win_probability else -config.avg_loss_r


def _simulate_path(
    config: SimulationConfig,
    risk_dollars: int,
    dynamic: bool,
    rng: np.random.Generator,
    consistency_cap: Optional[float],
    pad_on_breach: bool,
) -> PathResult:
    equity = 0.0
    peak = 0.0
    steps_taken = 0
    trades_executed = 0
    equities = [equity]
    trailing_floors = [peak - config.dd_limit]

    current_state = "normal"
    streak_remaining = 0
    streaks = config.streaks

    while steps_taken < config.max_steps:
        steps_taken += 1

        if rng.random() < streaks.no_trade_prob:
            equities.append(equity)
            trailing_floors.append(peak - config.dd_limit)
            continue

        if streak_remaining <= 0:
            current_state = "normal"
            roll = rng.random()
            if roll < streaks.hot_start_prob:
                current_state = "hot"
                streak_remaining = 1
                while rng.random() < streaks.hot_continue_prob:
                    streak_remaining += 1
            elif roll < streaks.hot_start_prob + streaks.cold_start_prob:
                current_state = "cold"
                streak_remaining = 1
                while rng.random() < streaks.cold_continue_prob:
                    streak_remaining += 1

        if current_state == "hot":
            p_win = min(0.95, config.win_rate + streaks.hot_shift)
        elif current_state == "cold":
            p_win = max(0.05, config.win_rate + streaks.cold_shift)
        else:
            p_win = config.win_rate

        if streak_remaining > 0:
            streak_remaining -= 1
            if streak_remaining == 0:
                current_state = "normal"

        current_risk = risk_dollars * 0.5 if dynamic and equity < peak else risk_dollars
        pnl = current_risk * _resolve_trade_outcome(config, rng, p_win)
        if consistency_cap is not None and pnl > 0:
            pnl = min(pnl, consistency_cap)

        equity += pnl
        peak = max(peak, equity)
        trades_executed += 1

        equities.append(equity)
        trailing_floors.append(peak - config.dd_limit)

        if equity < peak - config.dd_limit:
            if pad_on_breach:
                for _ in range(5):
                    equities.append(equity)
                    trailing_floors.append(peak - config.dd_limit)
            return PathResult(
                equities=np.array(equities),
                trailing_floors=np.array(trailing_floors),
                outcome="breach",
                steps_taken=steps_taken,
                trades_executed=trades_executed,
                final_equity=equity,
                peak_equity=peak,
            )

        if equity >= config.profit_target:
            return PathResult(
                equities=np.array(equities),
                trailing_floors=np.array(trailing_floors),
                outcome="pass",
                steps_taken=steps_taken,
                trades_executed=trades_executed,
                final_equity=equity,
                peak_equity=peak,
            )

    return PathResult(
        equities=np.array(equities),
        trailing_floors=np.array(trailing_floors),
        outcome="timeout",
        steps_taken=steps_taken,
        trades_executed=trades_executed,
        final_equity=equity,
        peak_equity=peak,
    )


def simulate_one_path(
    config: SimulationConfig,
    risk_dollars: int,
    dynamic: bool = False,
    seed: Optional[int] = None,
) -> PathResult:
    rng = np.random.default_rng(seed)
    return _simulate_path(
        config=config,
        risk_dollars=risk_dollars,
        dynamic=dynamic,
        rng=rng,
        consistency_cap=config.consistency_cap_amount,
        pad_on_breach=True,
    )


def run_simulation(
    config: SimulationConfig,
    risk_dollars: int,
    dynamic: bool = False,
    num_sims: Optional[int] = None,
) -> SimulationSummary:
    sim_count = num_sims or config.num_sims
    pass_count = 0
    breach_count = 0
    timeout_count = 0
    pass_steps: List[int] = []
    pass_trades: List[int] = []
    all_steps: List[int] = []
    all_trades: List[int] = []

    for sim_index in range(sim_count):
        rng = np.random.default_rng(sim_index)
        path = _simulate_path(
            config=config,
            risk_dollars=risk_dollars,
            dynamic=dynamic,
            rng=rng,
            consistency_cap=config.consistency_cap_amount,
            pad_on_breach=False,
        )
        all_steps.append(path.steps_taken)
        all_trades.append(path.trades_executed)

        if path.outcome == "pass":
            pass_count += 1
            pass_steps.append(path.steps_taken)
            pass_trades.append(path.trades_executed)
        elif path.outcome == "breach":
            breach_count += 1
        else:
            timeout_count += 1

    return SimulationSummary(
        risk_dollars=risk_dollars,
        dynamic=dynamic,
        total_runs=sim_count,
        pass_count=pass_count,
        breach_count=breach_count,
        timeout_count=timeout_count,
        pass_rate=round(pass_count / sim_count * 100.0, 1),
        breach_rate=round(breach_count / sim_count * 100.0, 1),
        timeout_rate=round(timeout_count / sim_count * 100.0, 1),
        avg_steps_to_pass=round(float(np.mean(pass_steps)), 1) if pass_steps else None,
        avg_trades_to_pass=round(float(np.mean(pass_trades)), 1) if pass_trades else None,
        avg_steps_all=round(float(np.mean(all_steps)), 1),
        avg_trades_all=round(float(np.mean(all_trades)), 1),
    )


def _score_style(summary: SimulationSummary, risk_dollars: int, style: TraderStyle) -> float:
    rules = STYLE_RULES[style]
    steps_value = (
        summary.avg_steps_to_pass if summary.avg_steps_to_pass is not None else summary.avg_steps_all
    )
    return (
        summary.pass_rate * rules["pass_weight"]
        - summary.breach_rate * rules["breach_weight"]
        - steps_value * rules["steps_weight"]
        + risk_dollars * rules["risk_weight"]
    )


def _style_risk_range(config: SimulationConfig, style: TraderStyle) -> range:
    rules = STYLE_RULES[style]
    min_risk = max(50, int(config.dd_limit * rules["min_risk_fraction"]))
    max_risk = int(config.dd_limit * rules["max_risk_fraction"])
    return range(min_risk, max_risk + config.risk_step, config.risk_step)


def _build_recommendation(
    label: str,
    rationale: str,
    risk_dollars: int,
    dynamic: bool,
    summary: SimulationSummary,
) -> Recommendation:
    return Recommendation(
        label=label,
        risk_dollars=risk_dollars,
        dynamic=dynamic,
        summary=summary,
        rationale=rationale,
    )


def get_style_recommendation(
    config: SimulationConfig,
    style: TraderStyle,
) -> Recommendation:
    best_summary: Optional[SimulationSummary] = None
    best_risk: Optional[int] = None
    best_score = float("-inf")
    fallback_summary: Optional[SimulationSummary] = None
    fallback_risk: Optional[int] = None
    fallback_pass_rate = -1.0
    min_required_pass_rate = STYLE_RULES[style]["min_pass_rate"]

    for risk in _style_risk_range(config, style):
        summary = run_simulation(
            config=config,
            risk_dollars=risk,
            dynamic=True,
            num_sims=config.recommendation_num_sims,
        )

        if summary.pass_rate > fallback_pass_rate:
            fallback_pass_rate = summary.pass_rate
            fallback_risk = risk
            fallback_summary = summary

        if summary.pass_rate < min_required_pass_rate:
            continue

        score = _score_style(summary, risk, style)
        if best_summary is None or score > best_score:
            best_summary = summary
            best_risk = risk
            best_score = score

    final_risk = best_risk if best_risk is not None else fallback_risk
    final_summary = best_summary if best_summary is not None else fallback_summary
    if final_risk is None or final_summary is None:
        final_risk = max(50, int(config.dd_limit * 0.10))
        final_summary = run_simulation(
            config=config,
            risk_dollars=final_risk,
            dynamic=True,
            num_sims=config.recommendation_num_sims,
        )

    return _build_recommendation(
        label=f"{style} Recommended",
        rationale=STYLE_DESCRIPTIONS[style],
        risk_dollars=final_risk,
        dynamic=True,
        summary=final_summary,
    )


def get_fastest_safe_recommendation(config: SimulationConfig) -> Recommendation:
    best_summary: Optional[SimulationSummary] = None
    best_risk = max(50, int(config.dd_limit * 0.05))
    best_score = float("-inf")
    for risk in range(best_risk, int(config.dd_limit) + config.risk_step, config.risk_step):
        summary = run_simulation(
            config=config,
            risk_dollars=risk,
            dynamic=True,
            num_sims=config.recommendation_num_sims,
        )
        if summary.pass_rate < 60.0 or summary.breach_rate > 40.0:
            continue

        score = (
            -(summary.avg_steps_to_pass or summary.avg_steps_all)
            + summary.pass_rate * 0.1
            - summary.breach_rate * 0.05
        )
        if best_summary is None:
            best_summary = summary
            best_risk = risk
            best_score = score
            continue
        if score > best_score:
            best_summary = summary
            best_risk = risk
            best_score = score

    if best_summary is None:
        fallback = get_style_recommendation(config, config.trader_style)
        return _build_recommendation(
            label="Fastest Safe",
            rationale="Falls back to the selected style when no plan meets the safety floor.",
            risk_dollars=fallback.risk_dollars,
            dynamic=True,
            summary=fallback.summary,
        )

    return _build_recommendation(
        label="Fastest Safe",
        rationale="Finds the quickest passing route that still clears the safety floor.",
        risk_dollars=best_risk,
        dynamic=True,
        summary=best_summary,
    )


def build_simulation_report(
    config: SimulationConfig,
    fixed_risk_amount: int,
) -> SimulationReport:
    fixed = _build_recommendation(
        label=f"Your Fixed ${fixed_risk_amount}",
        rationale="Uses the same dollar risk on every executed trade.",
        risk_dollars=fixed_risk_amount,
        dynamic=False,
        summary=run_simulation(config, fixed_risk_amount, dynamic=False, num_sims=config.num_sims),
    )
    dynamic = _build_recommendation(
        label=f"Your Dynamic ${fixed_risk_amount}",
        rationale="Uses full risk at highs and halves risk below the equity peak.",
        risk_dollars=fixed_risk_amount,
        dynamic=True,
        summary=run_simulation(config, fixed_risk_amount, dynamic=True, num_sims=config.num_sims),
    )
    aggressive = get_style_recommendation(config, "Aggressive")
    balanced = get_style_recommendation(config, "Balanced")
    conservative = get_style_recommendation(config, "Conservative")
    selected_map = {
        "Aggressive": aggressive,
        "Balanced": balanced,
        "Conservative": conservative,
    }
    fastest_safe = get_fastest_safe_recommendation(config)
    return SimulationReport(
        fixed=fixed,
        dynamic=dynamic,
        aggressive=aggressive,
        balanced=balanced,
        conservative=conservative,
        selected=selected_map[config.trader_style],
        fastest_safe=fastest_safe,
    )


def sample_paths(
    config: SimulationConfig,
    risk_dollars: int,
    dynamic: bool,
    count: int = 3,
    preferred_outcome: Optional[Outcome] = None,
    start_seed: int = 0,
    max_attempts: int = 500,
) -> List[PathResult]:
    paths: List[PathResult] = []
    seed = start_seed
    attempts = 0

    while len(paths) < count and attempts < max_attempts:
        path = simulate_one_path(
            config=config,
            risk_dollars=risk_dollars,
            dynamic=dynamic,
            seed=seed,
        )
        if preferred_outcome is None or path.outcome == preferred_outcome:
            paths.append(path)
        seed += 1
        attempts += 1

    if len(paths) < count and preferred_outcome is not None:
        seed = start_seed + max_attempts
        while len(paths) < count and attempts < max_attempts * 2:
            path = simulate_one_path(
                config=config,
                risk_dollars=risk_dollars,
                dynamic=dynamic,
                seed=seed,
            )
            paths.append(path)
            seed += 1
            attempts += 1

    return paths


__all__ = [
    "PathResult",
    "Recommendation",
    "SimulationConfig",
    "SimulationReport",
    "SimulationSummary",
    "StreakConfig",
    "STYLE_DESCRIPTIONS",
    "build_simulation_report",
    "calculate_expectancy",
    "get_fastest_safe_recommendation",
    "get_style_recommendation",
    "run_simulation",
    "sample_paths",
    "simulate_one_path",
]
