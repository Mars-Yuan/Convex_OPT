# ============ OCM 凸优单标的策略 Streamlit Dashboard ============
# 运行方式: streamlit run ocm_streamlit_Streamlit.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import backtrader as bt
import json
import os
import warnings
from datetime import date, datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone as ZoneInfo  # fallback for Python 3.8
import cvxpy as cp

warnings.filterwarnings('ignore', category=FutureWarning)


def get_yahoo_current_date():
    """获取 Yahoo Finance 数据源时区（美东时间）的当前日期"""
    try:
        eastern = ZoneInfo('America/New_York')
        now_eastern = datetime.now(eastern)
        return now_eastern.date()
    except Exception:
        return date.today()


# 页面配置
st.set_page_config(
    page_title="OCM 凸优单标的策略",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义样式
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00d4aa;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# 颜色主题
colors = {
    'strategy': '#9467bd',
    'benchmark': '#7f7f7f',
    'close': '#1f77b4',
    'trend': '#ff7f0e',
    'ema21': '#9467bd',
    'ema60': '#d62728',
    'alpha': '#2ca02c',
    'alpha_accel': '#d62728',
    'state_signal': '#17becf',
    'max_weight_cap': '#d62728',
    'floor_weight': '#2ca02c',
    'weight': '#8c564b',
    'positive': '#00d4aa',
    'negative': '#ff6b6b'
}

# =================== 策略参数 ===================
TREND_WINDOW = 80
TREND_LAMBDA = 20.0
VOL_WINDOW = 20
SIGNAL_SPAN = 5
RISK_AVERSION = 12.0
TURNOVER_PENALTY = 0.003
MAX_WEIGHT = 1.0
INITIAL_CASH = 100000.0
COMMISSION_RATE = 0.0000
SLIPPAGE_PCT = 0.0000

V2_CONSERVATIVE_MIN_WEIGHT = 0.45
V2_CONSERVATIVE_ALPHA_SCALE = 2.00
V2_ACCEL_WEIGHT = 0.35
V2_ADVANCED_UPTREND_MIN_WEIGHT = 0.55
V2_ADVANCED_RANGE_MAX_WEIGHT = 0.35
V2_ADVANCED_ALPHA_DEADZONE = 0.04
V2_ADVANCED_ALPHA_SCALE = 5.00
V2_ADVANCED_DEFAULT_RISK_MULTIPLIER = 0.65
V2_ADVANCED_DEFAULT_BEAR_PENALTY_MULTIPLIER = 1.00
V3_ALPHA_SCALE = 4.20
V3_ACCEL_WEIGHT = 0.42
V3_STATE_WEIGHT = 0.36
V3_NEG_GAP_PENALTY = 0.06
V3_POS_GAP_BONUS = 0.08
V3_UPTREND_MIN_WEIGHT = 0.50
V3_RANGE_MAX_WEIGHT = 0.80
V3_ALPHA_DEADZONE = 0.01
V3_RISK_MULTIPLIER = 0.48
V3_BEAR_PENALTY_MULTIPLIER = 0.84
V3_BEAR_CAP_PENALTY = 0.40
V3_V1_REFERENCE_RISK_MULTIPLIER = 0.72
V3_V1_REFERENCE_TURNOVER_MULTIPLIER = 0.55
V3_BLEND_BULL_BONUS = 0.95
V3_BLEND_ALPHA_BONUS = 0.28
V3_BLEND_RANGE_PENALTY = 0.34
V3_BLEND_BEAR_PENALTY = 0.90
V3_TARGET_TRACKING_STRENGTH = 4.80
V3_LEAD_ACCEL_BONUS = 1.05
V3_LEAD_STATE_BONUS = 0.42
V3_LEAD_ALPHA_BONUS = 0.26
V3_LEAD_NEG_GAP_PENALTY = 0.18
V3_LEAD_TO_V2_SHIFT = 0.88
V3_LEAD_CAP_BONUS = 0.12
V3_EXIT_ACCEL_BONUS = 0.98
V3_EXIT_BEAR_BONUS = 0.46
V3_EXIT_ALPHA_BONUS = 0.26
V3_EXIT_GAP_BONUS = 0.42
V3_EXIT_TO_V2_SHIFT = 0.82
V3_EXIT_CAP_PENALTY = 0.16
V3_UPSHIFT_TURNOVER_FLOOR = 0.08
V3_DOWNSHIFT_TURNOVER_FLOOR = 0.06
V2_STATE_FIT_PENALTY = 0.08
V2_STATE_GAP_SCALE = 0.08
DEFAULT_WARMUP_TRADING_DAYS = 160
DEFAULT_WARMUP_CALENDAR_DAYS = DEFAULT_WARMUP_TRADING_DAYS * 2
STRICT_WARMUP = True
STRICT_END_DATE_COVERAGE = False


# =================== 核心策略函数 ===================

def l1_trend_filter(prices, lam=20.0):
    y = np.asarray(prices, dtype=float)
    n = len(y)
    if n < 3:
        return y.copy()

    x = cp.Variable(n)
    d2 = np.diff(np.eye(n), 2, axis=0)
    objective = cp.Minimize(0.5 * cp.sum_squares(y - x) + lam * cp.norm1(d2 @ x))
    problem = cp.Problem(objective)

    try:
        problem.solve(solver=cp.OSQP, warm_start=True, verbose=False)
    except Exception:
        problem.solve(solver=cp.SCS, warm_start=True, verbose=False)

    if x.value is None:
        return y.copy()
    return np.asarray(x.value).ravel()


def solve_long_only_weight(alpha, sigma, previous_weight,
                           risk_aversion=12.0, turnover_penalty=0.003, max_weight=1.0):
    sigma = max(float(sigma), 1e-4)
    w = cp.Variable()
    objective = cp.Minimize(
        0.5 * risk_aversion * (sigma ** 2) * cp.square(w)
        - alpha * w
        + turnover_penalty * cp.abs(w - previous_weight)
    )
    constraints = [w >= 0.0, w <= max_weight]
    problem = cp.Problem(objective, constraints)

    try:
        problem.solve(solver=cp.OSQP, warm_start=True, verbose=False)
    except Exception:
        problem.solve(solver=cp.SCS, warm_start=True, verbose=False)

    if w.value is None:
        return float(previous_weight)
    return float(np.clip(w.value, 0.0, max_weight))


def infer_convex_state_weights(alpha, alpha_accel, trend_gap):
    target = np.array(
        [
            float(np.clip(alpha, -1.0, 1.0)),
            float(np.clip(alpha_accel, -1.0, 1.0)),
            float(np.clip(trend_gap / V2_STATE_GAP_SCALE, -1.0, 1.0)),
        ],
        dtype=float,
    )
    state_profiles = np.array(
        [
            [0.90, 0.05, -0.90],
            [0.25, 0.00, -0.25],
            [0.80, 0.00, -0.80],
        ],
        dtype=float,
    )
    prior = np.array([0.34, 0.33, 0.33], dtype=float)
    state_weights = cp.Variable(3)
    objective = cp.Minimize(
        cp.sum_squares(state_profiles @ state_weights - target)
        + V2_STATE_FIT_PENALTY * cp.sum_squares(state_weights - prior)
    )
    constraints = [state_weights >= 0.0, cp.sum(state_weights) == 1.0]
    problem = cp.Problem(objective, constraints)

    try:
        problem.solve(solver=cp.OSQP, warm_start=True, verbose=False)
    except Exception:
        problem.solve(solver=cp.SCS, warm_start=True, verbose=False)

    if state_weights.value is None:
        weights = prior.copy()
    else:
        weights = np.clip(np.asarray(state_weights.value).ravel(), 0.0, 1.0)
        weights = weights / (weights.sum() + 1e-8)

    bull_score, range_score, bear_score = weights.tolist()
    dominant_state = ['bull', 'range', 'bear'][int(np.argmax(weights))]
    return {
        'bull_score': float(bull_score),
        'range_score': float(range_score),
        'bear_score': float(bear_score),
        'state_signal': float(bull_score - bear_score),
        'dominant_state': dominant_state,
    }


def compute_convex_diagnostics(window_close, lam=20.0, signal_span=5):
    prices = np.asarray(window_close, dtype=float)
    log_price = np.log(prices)
    trend_log = l1_trend_filter(log_price, lam=lam)
    trend_price = np.exp(trend_log)

    span = int(min(signal_span, len(trend_log) - 1))
    if span < 1:
        alpha = 0.0
        alpha_accel = 0.0
        recent_slope = 0.0
        previous_slope = 0.0
    else:
        recent_slope = (trend_log[-1] - trend_log[-1 - span]) / span
        if len(trend_log) >= 2 * span + 1:
            previous_slope = (trend_log[-1 - span] - trend_log[-1 - 2 * span]) / span
        else:
            previous_slope = recent_slope
        hist_vol = np.std(np.diff(log_price)) + 1e-6
        alpha = np.tanh(recent_slope / hist_vol)
        alpha_accel = np.tanh((recent_slope - previous_slope) / hist_vol)

    trend_last = float(trend_price[-1])
    trend_gap = prices[-1] / trend_last - 1.0 if trend_last > 0 else 0.0
    state_info = infer_convex_state_weights(alpha, alpha_accel, trend_gap)

    return {
        'alpha': float(alpha),
        'alpha_accel': float(alpha_accel),
        'trend_last': trend_last,
        'trend_gap': float(trend_gap),
        'trend_series': trend_price,
        'recent_slope': float(recent_slope),
        'previous_slope': float(previous_slope),
        **state_info,
    }


def solve_single_asset_weight_hybrid(alpha, alpha_accel, trend_gap, sigma, previous_weight,
                                     bull_score, range_score, bear_score):
    sigma = max(float(sigma), 1e-4)

    raw_composite_alpha = (
        alpha
        + V3_ACCEL_WEIGHT * alpha_accel
        + V3_STATE_WEIGHT * (bull_score - bear_score)
        + V3_POS_GAP_BONUS * max(trend_gap, 0.0)
        - V3_NEG_GAP_PENALTY * max(-trend_gap, 0.0)
    )
    composite_alpha = V3_ALPHA_SCALE * raw_composite_alpha
    composite_alpha = 0.0 if abs(composite_alpha) < V3_ALPHA_DEADZONE else composite_alpha
    risk_aversion = RISK_AVERSION * (0.36 + 0.28 * range_score + 0.92 * bear_score) * V3_RISK_MULTIPLIER
    turnover_penalty = TURNOVER_PENALTY * (0.44 + 0.14 * range_score + 0.08 * bear_score)
    floor_cap = V3_UPTREND_MIN_WEIGHT
    base_weight_cap = float(np.clip(
        MAX_WEIGHT - (MAX_WEIGHT - V3_RANGE_MAX_WEIGHT) * range_score - V3_BEAR_CAP_PENALTY * bear_score,
        0.20,
        MAX_WEIGHT,
    ))

    lead_activation = float(np.clip(
        V3_LEAD_ACCEL_BONUS * max(alpha_accel, 0.0)
        + V3_LEAD_STATE_BONUS * max(bull_score - bear_score, 0.0)
        + V3_LEAD_ALPHA_BONUS * max(alpha, 0.0)
        - V3_LEAD_NEG_GAP_PENALTY * max(-trend_gap, 0.0),
        0.0,
        1.0,
    ))
    exit_activation = float(np.clip(
        V3_EXIT_ACCEL_BONUS * max(-alpha_accel, 0.0)
        + V3_EXIT_BEAR_BONUS * bear_score
        + V3_EXIT_ALPHA_BONUS * max(-alpha, 0.0)
        + V3_EXIT_GAP_BONUS * max(-trend_gap, 0.0),
        0.0,
        1.0,
    ))
    max_weight_cap = float(np.clip(
        base_weight_cap + V3_LEAD_CAP_BONUS * lead_activation - V3_EXIT_CAP_PENALTY * exit_activation,
        0.15,
        MAX_WEIGHT,
    ))

    v1_reference_weight = solve_long_only_weight(
        alpha=alpha,
        sigma=sigma,
        previous_weight=previous_weight,
        risk_aversion=RISK_AVERSION * V3_V1_REFERENCE_RISK_MULTIPLIER,
        turnover_penalty=TURNOVER_PENALTY * V3_V1_REFERENCE_TURNOVER_MULTIPLIER,
        max_weight=MAX_WEIGHT,
    )
    v2_reference_weight = solve_long_only_weight(
        alpha=composite_alpha,
        sigma=sigma,
        previous_weight=previous_weight,
        risk_aversion=risk_aversion,
        turnover_penalty=turnover_penalty * (1.0 - 0.28 * lead_activation - 0.24 * exit_activation),
        max_weight=max_weight_cap,
    )
    mature_trend_to_v1 = float(np.clip(
        0.16
        + V3_BLEND_BULL_BONUS * bull_score
        + V3_BLEND_ALPHA_BONUS * max(alpha, 0.0)
        - V3_BLEND_RANGE_PENALTY * range_score
        - V3_BLEND_BEAR_PENALTY * bear_score,
        0.05,
        0.95,
    ))
    blend_to_v1 = float(np.clip(
        mature_trend_to_v1 - V3_LEAD_TO_V2_SHIFT * lead_activation - V3_EXIT_TO_V2_SHIFT * exit_activation,
        0.02,
        0.95,
    ))
    blend_target_weight = float(np.clip(
        blend_to_v1 * v1_reference_weight + (1.0 - blend_to_v1) * v2_reference_weight,
        0.0,
        max_weight_cap,
    ))
    desired_floor = min(
        floor_cap,
        max(
            0.0,
            0.55 * blend_target_weight + 0.08 * bull_score - 0.08 * bear_score + 0.08 * lead_activation - 0.06 * exit_activation,
        ),
    )
    tracking_strength = V3_TARGET_TRACKING_STRENGTH * float(np.clip(
        0.60 + 0.35 * bull_score + 0.22 * max(alpha, 0.0) + 0.35 * lead_activation + 0.42 * exit_activation,
        0.55,
        1.70,
    ))
    up_turnover_penalty = turnover_penalty * float(np.clip(0.42 - 0.34 * lead_activation, V3_UPSHIFT_TURNOVER_FLOOR, 0.60))
    down_turnover_penalty = turnover_penalty * float(np.clip(0.36 - 0.30 * exit_activation, V3_DOWNSHIFT_TURNOVER_FLOOR, 0.58))

    target_weight = cp.Variable()
    floor_weight = cp.Variable()
    objective = cp.Minimize(
        0.5 * risk_aversion * (sigma ** 2) * cp.square(target_weight)
        - composite_alpha * target_weight
        + up_turnover_penalty * cp.pos(target_weight - previous_weight)
        + down_turnover_penalty * cp.pos(previous_weight - target_weight)
        + 3.5 * cp.square(floor_weight - desired_floor)
        + 2.5 * cp.square(target_weight - floor_weight)
        + (0.50 * V3_BEAR_PENALTY_MULTIPLIER) * bear_score * target_weight
        + tracking_strength * cp.square(target_weight - blend_target_weight)
    )
    constraints = [
        target_weight >= 0.0,
        target_weight <= max_weight_cap,
        floor_weight >= 0.0,
        floor_weight <= floor_cap,
        floor_weight <= target_weight,
    ]
    problem = cp.Problem(objective, constraints)

    try:
        problem.solve(solver=cp.OSQP, warm_start=True, verbose=False)
    except Exception:
        problem.solve(solver=cp.SCS, warm_start=True, verbose=False)

    if target_weight.value is None or floor_weight.value is None:
        resolved_weight = float(np.clip(previous_weight, 0.0, max_weight_cap))
        resolved_floor = float(min(desired_floor, resolved_weight))
    else:
        resolved_weight = float(np.clip(target_weight.value, 0.0, max_weight_cap))
        resolved_floor = float(np.clip(floor_weight.value, 0.0, min(floor_cap, resolved_weight)))

    return {
        'target_weight': resolved_weight,
        'floor_weight': resolved_floor,
        'desired_floor': float(desired_floor),
        'composite_alpha': float(composite_alpha),
        'raw_composite_alpha': float(raw_composite_alpha),
        'max_weight_cap': float(max_weight_cap),
        'v1_reference_weight': float(v1_reference_weight),
        'v2_reference_weight': float(v2_reference_weight),
        'blend_to_v1': float(blend_to_v1),
        'blend_target_weight': float(blend_target_weight),
        'tracking_strength': float(tracking_strength),
        'lead_activation': float(lead_activation),
        'exit_activation': float(exit_activation),
        'up_turnover_penalty': float(up_turnover_penalty),
        'down_turnover_penalty': float(down_turnover_penalty),
    }


def solve_single_asset_weight_v2(alpha, alpha_accel, trend_gap, sigma, previous_weight,
                                 bull_score, range_score, bear_score, profile='v3'):
    return solve_single_asset_weight_hybrid(
        alpha=alpha,
        alpha_accel=alpha_accel,
        trend_gap=trend_gap,
        sigma=sigma,
        previous_weight=previous_weight,
        bull_score=bull_score,
        range_score=range_score,
        bear_score=bear_score,
    )


def calc_performance_metrics(portfolio_value, benchmark_curve, strategy_label, benchmark_label):
    strategy_df = pd.DataFrame(index=portfolio_value.index)
    strategy_df['portfolio_value'] = portfolio_value.astype(float)
    strategy_df['portfolio_return'] = strategy_df['portfolio_value'].pct_change().fillna(0.0)
    base_value = float(strategy_df['portfolio_value'].iloc[0])
    strategy_df['equity_curve'] = strategy_df['portfolio_value'] / base_value
    strategy_df['benchmark_curve'] = benchmark_curve.reindex(strategy_df.index).ffill()

    trading_days = max(len(strategy_df), 1)
    total_return = strategy_df['equity_curve'].iloc[-1] - 1.0
    ann_return = (1.0 + total_return) ** (252.0 / trading_days) - 1.0 if trading_days > 1 else total_return
    ann_vol = strategy_df['portfolio_return'].std() * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol > 0 else np.nan
    max_drawdown = (strategy_df['equity_curve'] / strategy_df['equity_curve'].cummax() - 1.0).min()

    bench_returns = strategy_df['benchmark_curve'].pct_change().fillna(0.0)
    bench_total_return = strategy_df['benchmark_curve'].iloc[-1] - 1.0
    bench_ann_return = (1.0 + bench_total_return) ** (252.0 / trading_days) - 1.0 if trading_days > 1 else bench_total_return
    bench_ann_vol = bench_returns.std() * np.sqrt(252)
    bench_sharpe = bench_ann_return / bench_ann_vol if bench_ann_vol > 0 else np.nan
    bench_drawdown = (strategy_df['benchmark_curve'] / strategy_df['benchmark_curve'].cummax() - 1.0).min()

    comparison = pd.DataFrame(
        {
            '总收益': [total_return, bench_total_return],
            '年化收益': [ann_return, bench_ann_return],
            '年化波动': [ann_vol, bench_ann_vol],
            'Sharpe': [sharpe, bench_sharpe],
            '最大回撤': [max_drawdown, bench_drawdown],
        },
        index=[strategy_label, benchmark_label],
    )
    return strategy_df, comparison


# =================== ADX 指标函数 (thinkScript 转 Python) ===================

def wilders_average(series, length):
    values = pd.Series(series, dtype=float).reset_index(drop=True)
    result = pd.Series(np.nan, index=values.index, dtype=float)
    if len(values) < length:
        return result
    first_avg = values.iloc[:length].mean()
    result.iloc[length - 1] = first_avg
    alpha_val = 1.0 / length
    for idx in range(length, len(values)):
        result.iloc[idx] = alpha_val * values.iloc[idx] + (1.0 - alpha_val) * result.iloc[idx - 1]
    return result


def inertia(series, length):
    values = pd.Series(series, dtype=float).reset_index(drop=True)
    result = pd.Series(np.nan, index=values.index, dtype=float)
    if len(values) < length:
        return result
    x = np.arange(1, length + 1, dtype=float)
    x_mean = x.mean()
    denom = np.sum((x - x_mean) ** 2)
    for idx in range(length - 1, len(values)):
        window = values.iloc[idx - length + 1: idx + 1]
        if window.isna().any():
            continue
        y = window.to_numpy(dtype=float)
        y_mean = y.mean()
        slope = np.sum((x - x_mean) * (y - y_mean)) / denom
        intercept = y_mean - slope * x_mean
        result.iloc[idx] = slope * x[-1] + intercept
    return result


def compute_tos_adx(ohlc_df, length=14):
    high = pd.Series(ohlc_df['high'], dtype=float).reset_index(drop=True)
    low = pd.Series(ohlc_df['low'], dtype=float).reset_index(drop=True)
    close = pd.Series(ohlc_df['close'], dtype=float).reset_index(drop=True)
    prev_close = close.shift(1).fillna(close)

    tr_raw = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    tr1 = wilders_average(tr_raw, length)

    hd = high - high.shift(1)
    ld = low.shift(1) - low
    dmp_raw = pd.Series(np.where((hd > 0) & (hd > ld), hd, 0.0), dtype=float)
    dmm_raw = pd.Series(np.where((ld > 0) & (ld > hd), ld, 0.0), dtype=float)

    dmp = wilders_average(dmp_raw, length)
    dmm = wilders_average(dmm_raw, length)

    pdi = (dmp * 100.0 / tr1).replace([np.inf, -np.inf], np.nan)
    mdi = (dmm * 100.0 / tr1).replace([np.inf, -np.inf], np.nan)
    pdi2 = inertia(pdi, 7)
    mdi2 = inertia(mdi, 7)

    denom_val = (mdi + pdi).replace(0.0, np.nan)
    dx = ((mdi - pdi).abs() / denom_val) * 100.0
    adx = wilders_average(dx, length)
    adx2 = inertia(adx, 7)

    buy_signal = pd.Series(
        np.where(
            (adx > 10) & (adx.shift(1) <= 10) & (pdi > mdi)
            & ((pdi - mdi) > (pdi.shift(1) - mdi.shift(1))),
            adx, np.nan,
        ),
        dtype=float,
    )

    result = pd.DataFrame({
        'PDI': pdi, 'PDI2': pdi2, 'MDI': mdi, 'MDI2': mdi2,
        'ADX': adx, 'ADX2': adx2, 'BuySignal': buy_signal,
    })
    result.index = ohlc_df.index
    return result


# =================== 数据获取 ===================

def fetch_daily_history(symbol, start_date=None, end_date=None):
    download_end = None
    if end_date is not None:
        download_end = pd.Timestamp(end_date) + pd.Timedelta(days=1)

    df = yf.download(
        symbol, start=start_date, end=download_end,
        interval='1d', auto_adjust=False, actions=False,
        progress=False, threads=False
    )

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    rename_map = {
        'Open': 'open', 'High': 'high', 'Low': 'low',
        'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
    }
    df = df.rename(columns=rename_map)

    required_cols = ['open', 'high', 'low', 'close']
    if any(col not in df.columns for col in required_cols):
        return None
    if 'volume' not in df.columns:
        df['volume'] = 0

    df.index = pd.to_datetime(df.index)
    if getattr(df.index, 'tz', None) is not None:
        df.index = df.index.tz_localize(None)
    df.index.name = 'datetime'
    df = df[['open', 'high', 'low', 'close', 'volume']].sort_index()
    df = df[~df.index.duplicated(keep='last')]
    df = df[df['close'] > 0]
    return df if not df.empty else None


def validate_formal_coverage(formal_history, requested_end, strict=False, label='正式回测区间'):
    if formal_history.empty:
        raise ValueError(f'{label}为空，无法校验结束日覆盖情况')

    actual_last_date = pd.Timestamp(formal_history.index[-1]).date()
    requested_end_date = pd.Timestamp(requested_end).date()
    coverage_ok = actual_last_date >= requested_end_date

    if coverage_ok:
        msg = f'{label}结束日覆盖校验通过: 实际最后日期 {actual_last_date}，请求结束日期 {requested_end_date}'
    else:
        msg = (
            f'{label}结束日覆盖不足: 实际最后日期 {actual_last_date}，早于请求结束日期 {requested_end_date}。'
            '可能原因是请求日尚未收盘、交易日未结束、节假日或数据源延迟。'
        )
        if strict:
            raise ValueError(msg)

    return coverage_ok, msg, actual_last_date


def ensure_history_with_warmup(symbol, data_start, data_end, required_warmup_bars, strict=True):
    local_fetch_start = pd.Timestamp(data_start) - timedelta(days=DEFAULT_WARMUP_CALENDAR_DAYS)
    history = fetch_daily_history(symbol, start_date=local_fetch_start, end_date=data_end)
    if history is None or history.empty:
        raise ValueError(f'未获取到 {symbol} 的历史数据，请检查标的代码或日期范围')

    available_bars = int((history.index < pd.Timestamp(data_start)).sum())
    expansion_round = 0
    while available_bars < required_warmup_bars and expansion_round < 4:
        expansion_round += 1
        expanded_calendar_days = max(
            DEFAULT_WARMUP_CALENDAR_DAYS * (expansion_round + 1),
            required_warmup_bars * (3 + expansion_round)
        )
        local_fetch_start = pd.Timestamp(data_start) - timedelta(days=expanded_calendar_days)
        history = fetch_daily_history(symbol, start_date=local_fetch_start, end_date=data_end)
        if history is None or history.empty:
            break
        available_bars = int((history.index < pd.Timestamp(data_start)).sum())

    if history is None or history.empty:
        raise ValueError(f'未获取到 {symbol} 的历史数据，请检查标的代码或日期范围')

    if available_bars < required_warmup_bars:
        msg = (
            f'预热样本仍不足: 当前 {available_bars} 条，要求 {required_warmup_bars} 条。'
            f'已向前扩展到 {pd.Timestamp(local_fetch_start).date()}，请检查标的上市时间或放宽窗口参数。'
        )
        if strict:
            raise ValueError(msg)
        warnings.warn(msg)

    return history, pd.Timestamp(local_fetch_start), available_bars


# =================== 回测引擎（Backtrader 成交逻辑）===================


class YahooPandasData(bt.feeds.PandasData):
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )

def run_single_asset_backtest(history_df, data_start, data_end):
    """单标的 V3 Hybrid 策略回测。"""
    min_bars = max(TREND_WINDOW, VOL_WINDOW + 1, SIGNAL_SPAN * 2 + 2)
    start_ts = pd.Timestamp(data_start)
    end_ts = pd.Timestamp(data_end)

    bt_df = history_df[['open', 'high', 'low', 'close', 'volume']].copy()
    bt_df.index = pd.to_datetime(bt_df.index).tz_localize(None)

    class SingleAssetV3Strategy(bt.Strategy):
        params = dict(
            trend_window=TREND_WINDOW,
            trend_lambda=TREND_LAMBDA,
            vol_window=VOL_WINDOW,
            signal_span=SIGNAL_SPAN,
            backtest_start=start_ts,
            backtest_end=end_ts,
        )

        def __init__(self):
            self.order = None
            self.previous_target_weight = 0.0
            self.records = []

        def notify_order(self, order):
            if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
                self.order = None

        def next(self):
            current_dt = bt.num2date(self.datas[0].datetime[0]).replace(tzinfo=None)
            current_close = float(self.data.close[0])
            portfolio_value = float(self.broker.getvalue())
            position_value = float(self.position.size * current_close)
            actual_weight = position_value / portfolio_value if portfolio_value > 0 else 0.0
            in_formal_window = self.p.backtest_start <= pd.Timestamp(current_dt) <= self.p.backtest_end

            if len(self) < min_bars:
                self.records.append({
                    'datetime': current_dt,
                    'close': current_close,
                    'trend': np.nan,
                    'alpha': 0.0,
                    'alpha_accel': 0.0,
                    'bull_score': np.nan,
                    'range_score': np.nan,
                    'bear_score': np.nan,
                    'state_signal': 0.0,
                    'dominant_state': 'warmup',
                    'raw_composite_alpha': np.nan,
                    'composite_alpha': np.nan,
                    'max_weight_cap': np.nan,
                    'target_weight': actual_weight,
                    'floor_weight': 0.0,
                    'desired_floor': 0.0,
                    'blend_to_v1': np.nan,
                    'blend_target_weight': np.nan,
                    'lead_activation': np.nan,
                    'exit_activation': np.nan,
                    'actual_weight': actual_weight,
                    'portfolio_value': portfolio_value,
                    'in_formal_window': in_formal_window,
                })
                return

            hist_close = np.array(self.data.close.get(size=self.p.trend_window), dtype=float)
            vol_close = np.array(self.data.close.get(size=self.p.vol_window + 1), dtype=float)
            hist_returns = pd.Series(vol_close).pct_change().dropna()
            sigma = float(hist_returns.std() * np.sqrt(252))

            diag = compute_convex_diagnostics(
                hist_close,
                lam=self.p.trend_lambda,
                signal_span=self.p.signal_span,
            )
            allocation = solve_single_asset_weight_hybrid(
                alpha=diag['alpha'],
                alpha_accel=diag['alpha_accel'],
                trend_gap=diag['trend_gap'],
                sigma=sigma,
                previous_weight=self.previous_target_weight,
                bull_score=diag['bull_score'],
                range_score=diag['range_score'],
                bear_score=diag['bear_score'],
            )
            target_weight = allocation['target_weight']

            if not in_formal_window:
                target_weight = 0.0

            if self.order is None:
                self.order = self.order_target_percent(target=target_weight)

            self.previous_target_weight = target_weight
            self.records.append({
                'datetime': current_dt,
                'close': current_close,
                'trend': float(diag['trend_last']),
                'alpha': float(diag['alpha']),
                'alpha_accel': float(diag['alpha_accel']),
                'bull_score': float(diag['bull_score']),
                'range_score': float(diag['range_score']),
                'bear_score': float(diag['bear_score']),
                'state_signal': float(diag['state_signal']),
                'dominant_state': diag['dominant_state'],
                'raw_composite_alpha': float(allocation['raw_composite_alpha']),
                'composite_alpha': float(allocation['composite_alpha']),
                'max_weight_cap': float(allocation['max_weight_cap']),
                'target_weight': float(target_weight),
                'floor_weight': float(allocation['floor_weight']),
                'desired_floor': float(allocation['desired_floor']),
                'blend_to_v1': float(allocation['blend_to_v1']),
                'blend_target_weight': float(allocation['blend_target_weight']),
                'lead_activation': float(allocation['lead_activation']),
                'exit_activation': float(allocation['exit_activation']),
                'actual_weight': float(actual_weight),
                'portfolio_value': float(portfolio_value),
                'in_formal_window': in_formal_window,
            })

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(INITIAL_CASH)
    cerebro.broker.setcommission(commission=COMMISSION_RATE)
    cerebro.broker.set_slippage_perc(SLIPPAGE_PCT)
    cerebro.adddata(YahooPandasData(dataname=bt_df), name='single_asset')
    cerebro.addstrategy(SingleAssetV3Strategy)

    results = cerebro.run()
    strategy = results[0]
    full_df = pd.DataFrame(strategy.records).set_index('datetime')
    full_df.index = pd.to_datetime(full_df.index)
    formal_df = full_df.loc[(full_df.index >= start_ts) & (full_df.index <= end_ts)].copy()

    if formal_df.empty:
        return None

    formal_df['ema21'] = formal_df['close'].ewm(span=21, adjust=False).mean()
    formal_df['ema60'] = formal_df['close'].ewm(span=60, adjust=False).mean()

    return formal_df


# =================== 构建运行时数据 ===================

@st.cache_data(show_spinner=False, ttl=300)
def build_runtime_data(symbol, start_date_input, end_date_input):
    data_start = pd.Timestamp(start_date_input)
    data_end = pd.Timestamp(end_date_input)

    # 验证标的
    try:
        ticker = yf.Ticker(symbol)
        test_hist = ticker.history(period='5d')
        if test_hist.empty:
            return None, "标的代码错误或 Yahoo 无此标的，请重新输入"
    except Exception as e:
        return None, f"标的验证失败: {str(e)}"

    required_warmup_bars = max(TREND_WINDOW, VOL_WINDOW + 1, SIGNAL_SPAN * 2 + 2)
    try:
        history, fetch_start, available_warmup = ensure_history_with_warmup(
            symbol=symbol,
            data_start=data_start,
            data_end=data_end,
            required_warmup_bars=required_warmup_bars,
            strict=STRICT_WARMUP,
        )
    except Exception as e:
        return None, str(e)

    formal_count = int(((history.index >= data_start) & (history.index <= data_end)).sum())
    if formal_count < 10:
        return None, "正式回测区间有效交易日不足"

    # 运行回测
    result_df = run_single_asset_backtest(history, data_start, data_end)
    if result_df is None or result_df.empty:
        return None, "回测结果为空，请检查参数"

    coverage_ok, coverage_msg, actual_last_date = validate_formal_coverage(
        result_df,
        data_end,
        strict=STRICT_END_DATE_COVERAGE,
        label='V3 Hybrid 正式回测区间',
    )

    # 计算 ADX
    formal_history = history.loc[
        (history.index >= result_df.index[0]) & (history.index <= result_df.index[-1])
    ].copy()
    adx_df = compute_tos_adx(formal_history[['high', 'low', 'close']], length=14)
    result_df = result_df.join(adx_df, how='left')

    benchmark_curve = result_df['close'] / float(result_df['close'].iloc[0])
    perf_df, perf_table = calc_performance_metrics(
        portfolio_value=result_df['portfolio_value'],
        benchmark_curve=benchmark_curve,
        strategy_label='V3 Hybrid',
        benchmark_label='Buy & Hold',
    )
    result_df['equity_curve'] = perf_df['equity_curve']
    result_df['buy_hold_curve'] = perf_df['benchmark_curve']

    # 计算绩效指标
    strategy_stats = perf_table.loc['V3 Hybrid']
    benchmark_stats = perf_table.loc['Buy & Hold']
    state_counts = result_df['dominant_state'].value_counts().to_dict()

    # 构建返回数据
    dates = result_df.index.strftime('%Y-%m-%d').tolist()

    def safe_list(series_name):
        if series_name in result_df.columns:
            return [None if (isinstance(v, float) and np.isnan(v)) else v
                    for v in result_df[series_name].values.tolist()]
        return []

    runtime_data = {
        'symbol': symbol,
        'dates': dates,
        'equity_curve': result_df['equity_curve'].values.tolist(),
        'buy_hold_curve': result_df['buy_hold_curve'].values.tolist(),
        'close': result_df['close'].values.tolist(),
        'trend': safe_list('trend'),
        'ema21': safe_list('ema21'),
        'ema60': safe_list('ema60'),
        'alpha': result_df['alpha'].values.tolist(),
        'alpha_accel': result_df['alpha_accel'].values.tolist(),
        'bull_score': safe_list('bull_score'),
        'range_score': safe_list('range_score'),
        'bear_score': safe_list('bear_score'),
        'state_signal': safe_list('state_signal'),
        'dominant_state': result_df['dominant_state'].values.tolist(),
        'raw_composite_alpha': safe_list('raw_composite_alpha'),
        'composite_alpha': safe_list('composite_alpha'),
        'max_weight_cap': safe_list('max_weight_cap'),
        'floor_weight': safe_list('floor_weight'),
        'desired_floor': safe_list('desired_floor'),
        'blend_to_v1': safe_list('blend_to_v1'),
        'blend_target_weight': safe_list('blend_target_weight'),
        'lead_activation': safe_list('lead_activation'),
        'exit_activation': safe_list('exit_activation'),
        'target_weight': result_df['target_weight'].values.tolist(),
        'actual_weight': result_df['actual_weight'].values.tolist(),
        'PDI2': safe_list('PDI2'),
        'MDI2': safe_list('MDI2'),
        'ADX': safe_list('ADX'),
        'BuySignal': safe_list('BuySignal'),
        'strategy_result': {
            'total_return': float(strategy_stats['总收益']),
            'ann_return': float(strategy_stats['年化收益']),
            'ann_vol': float(strategy_stats['年化波动']),
            'sharpe': float(strategy_stats['Sharpe']) if pd.notna(strategy_stats['Sharpe']) else 0.0,
            'max_drawdown': float(strategy_stats['最大回撤']),
        },
        'benchmark_result': {
            'total_return': float(benchmark_stats['总收益']),
            'ann_return': float(benchmark_stats['年化收益']),
            'ann_vol': float(benchmark_stats['年化波动']),
            'sharpe': float(benchmark_stats['Sharpe']) if pd.notna(benchmark_stats['Sharpe']) else 0.0,
            'max_drawdown': float(benchmark_stats['最大回撤']),
        },
        'state_counts': state_counts,
        'warmup_bars': available_warmup,
        'fetch_start': fetch_start.strftime('%Y-%m-%d'),
        'formal_start': result_df.index[0].strftime('%Y-%m-%d'),
        'formal_end': result_df.index[-1].strftime('%Y-%m-%d'),
        'coverage_ok': coverage_ok,
        'coverage_msg': coverage_msg,
        'actual_last_date': actual_last_date.strftime('%Y-%m-%d'),
    }

    return runtime_data, None


# =================== 主函数 ===================

def main():
    st.markdown(
        '<h1 style="text-align: center;">OPT Convex 策略 '
        '<span style="font-size: 0.5em; color: #888888;">V5.2</span></h1>',
        unsafe_allow_html=True
    )

    today = get_yahoo_current_date()
    default_start_date = date(today.year - 1, 1, 1)
    default_end_date = today

    col_info1, col_info2, col_info3 = st.columns([1.4, 1, 1])
    with col_info1:
        symbol_input = st.text_input("标的", value="SPY", key='symbol_input_main')
    with col_info2:
        start_date_input = st.date_input("开始日期", value=default_start_date, key='start_date_input_main')
    with col_info3:
        end_date_input = st.date_input("结束日期", value=default_end_date, key='end_date_input_main')

    st.divider()

    # 构建数据
    with st.spinner('正在计算策略（OPT Convex V5.2 仓位求解）...'):
        runtime_data, runtime_error = build_runtime_data(symbol_input, start_date_input, end_date_input)

    if runtime_error:
        st.error(f"⚠️ {runtime_error}")
        return
    if runtime_data is None:
        st.error("⚠️ 未获取到数据")
        return

    data = runtime_data
    sr = data['strategy_result']
    br = data['benchmark_result']

    # ========== 统计卡片 ==========
    st.markdown(
        f"### 策略表现概览 <span style='font-size: 0.7em; color: #888888;'>"
        f"{data['symbol']}</span>",
        unsafe_allow_html=True
    )

    st.markdown("**OPT Convex 策略 V5.2**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "总收益率", f"{sr['total_return']:.2%}",
            delta=f"vs 基准 {sr['total_return'] - br['total_return']:.2%}"
        )
    with col2:
        st.metric(
            "年化收益", f"{sr['ann_return']:.2%}",
            delta=f"vs 基准 {sr['ann_return'] - br['ann_return']:.2%}"
        )
    with col3:
        st.metric(
            "Sharpe Ratio", f"{sr['sharpe']:.2f}",
            delta=f"vs 基准 {sr['sharpe'] - br['sharpe']:.2f}"
        )
    with col4:
        st.metric(
            "最大回撤", f"{sr['max_drawdown']:.2%}",
            delta=f"vs 基准 {sr['max_drawdown'] - br['max_drawdown']:.2%}",
            delta_color="inverse"
        )

    state_str = " / ".join([f"{k}: {v}天" for k, v in data.get('state_counts', {}).items()])
    st.caption(
        f"预热样本: {data['warmup_bars']}条 | 预热起点: {data['fetch_start']} | "
        f"正式区间: {data['formal_start']} ~ {data['formal_end']}"
    )
    st.caption(f"状态分布: {state_str} | 结束日覆盖: {data['coverage_msg']}")

    st.markdown("**基准 (买入持有)**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总收益率", f"{br['total_return']:.2%}")
    with col2:
        st.metric("年化收益", f"{br['ann_return']:.2%}")
    with col3:
        st.metric("Sharpe Ratio", f"{br['sharpe']:.2f}")
    with col4:
        st.metric("最大回撤", f"{br['max_drawdown']:.2%}")

    st.divider()

    # ========== 净值曲线 ==========
    st.markdown(
        f"### 净值曲线 <span style='font-size: 0.7em; color: #888888;'>{data['symbol']}</span>",
        unsafe_allow_html=True
    )

    dates = data['dates']

    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(
        x=dates, y=data['equity_curve'],
        name='OPT Convex 策略 V5.2', line=dict(color=colors['strategy'], width=2.5)
    ))
    fig_equity.add_trace(go.Scatter(
        x=dates, y=data['buy_hold_curve'],
        name='买入持有', line=dict(color=colors['benchmark'], width=1.5)
    ))
    fig_equity.update_layout(
        template='plotly_dark', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center'),
        margin=dict(l=20, r=20, t=40, b=40), height=380,
        yaxis_title='净值',
    )
    st.plotly_chart(fig_equity, use_container_width=True)

    st.divider()

    # ========== 价格 + 趋势 + 仓位 + ADX ==========
    st.markdown(
        f"### 价格·趋势·仓位·ADX <span style='font-size: 0.7em; color: #888888;'>{data['symbol']}</span>",
        unsafe_allow_html=True
    )

    adx_data = data.get('ADX', [])
    has_adx = adx_data and any(v is not None for v in adx_data)

    if has_adx:
        fig_combined = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.62, 0.38],
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        )
    else:
        fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

    fig_combined.add_trace(go.Scatter(
        x=dates, y=data['close'], name='Close',
        line=dict(color=colors['close'], width=1.2)
    ), row=1, col=1, secondary_y=False)

    fig_combined.add_trace(go.Scatter(
        x=dates, y=data['ema21'], name='EMA 21',
        line=dict(color=colors['ema21'], width=1.0)
    ), row=1, col=1, secondary_y=False)

    fig_combined.add_trace(go.Scatter(
        x=dates, y=data['ema60'], name='EMA 60',
        line=dict(color=colors['ema60'], width=1.0)
    ), row=1, col=1, secondary_y=False)

    fig_combined.add_trace(go.Scatter(
        x=dates, y=data['trend'], name='L1 Trend',
        line=dict(color=colors['trend'], width=0.5, dash='dot')
    ), row=1, col=1, secondary_y=False)

    fig_combined.add_trace(go.Scatter(
        x=dates, y=data['target_weight'], name='目标仓位',
        fill='tozeroy', line=dict(color='#d9d9d9', width=0.5), opacity=0.30,
    ), row=1, col=1, secondary_y=True)

    if has_adx:
        fig_combined.add_trace(go.Scatter(
            x=dates, y=data['PDI2'], name='PDI2',
            line=dict(color='#d62728', width=1.1)
        ), row=2, col=1)
        fig_combined.add_trace(go.Scatter(
            x=dates, y=data['MDI2'], name='MDI2',
            line=dict(color='#2ca02c', width=1.1)
        ), row=2, col=1)
        fig_combined.add_trace(go.Scatter(
            x=dates, y=data['ADX'], name='ADX',
            line=dict(color='#f1c40f', width=1.2)
        ), row=2, col=1)
        fig_combined.add_hline(y=10, line_dash="dash", line_color="#1f77b4", annotation_text="10", row=2, col=1)
        fig_combined.add_hline(y=20, line_dash="dash", line_color="#1f77b4", annotation_text="20", row=2, col=1)
        fig_combined.add_hline(y=40, line_dash="dash", line_color="#1f77b4", annotation_text="40", row=2, col=1)

        buy_signals = data.get('BuySignal', [])
        buy_x = [dates[i] for i in range(len(buy_signals)) if buy_signals[i] is not None]
        buy_y = [v for v in buy_signals if v is not None]
        if buy_x:
            fig_combined.add_trace(go.Scatter(
                x=buy_x, y=buy_y, mode='markers', name='Buy Signal',
                marker=dict(color='#17becf', size=8, symbol='triangle-up')
            ), row=2, col=1)

    fig_combined.update_layout(
        template='plotly_dark', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center'),
        margin=dict(l=20, r=20, t=40, b=40), height=650 if has_adx else 400,
    )
    fig_combined.update_yaxes(title_text="价格 ($)", row=1, col=1, secondary_y=False)
    fig_combined.update_yaxes(title_text="仓位", range=[0, 1.05], row=1, col=1, secondary_y=True)
    if has_adx:
        fig_combined.update_xaxes(showticklabels=True, row=1, col=1)
        fig_combined.update_yaxes(title_text='ADX', row=2, col=1)
        fig_combined.update_xaxes(title_text='日期', row=2, col=1)
    else:
        fig_combined.update_xaxes(title_text='日期', row=1, col=1)

    st.plotly_chart(fig_combined, use_container_width=True)

    if not has_adx:
        st.info("ADX 数据不可用")

    st.divider()

    # ========== 交易明细表 ==========
    st.markdown(
        f"### 交易明细表 <span style='font-size: 0.7em; color: #888888;'>{data['symbol']}</span>",
        unsafe_allow_html=True
    )

    # 最近数据日期
    if dates:
        st.caption(f"数据最新日期: {dates[-1]}")

    # 按 notebook 逻辑构建交易明细：筛选有实际仓位变化的交易日，倒序仅保留 30 行
    threshold = 1e-4
    trade_df = pd.DataFrame({
        '日期': pd.to_datetime(dates),
        '收盘价': data['close'],
        'actual_weight': data['actual_weight'],
        'dominant_state': data['dominant_state'],
        'composite_alpha': data['composite_alpha'],
        'state_signal': data['state_signal'],
    })

    trade_df['前一日实际仓位'] = trade_df['actual_weight'].shift(1).fillna(0.0)
    trade_df['当日实际仓位'] = trade_df['actual_weight']
    trade_df['实际仓位变化'] = trade_df['当日实际仓位'] - trade_df['前一日实际仓位']
    trade_df['交易方向'] = np.where(
        trade_df['实际仓位变化'] > threshold,
        '买入',
        np.where(trade_df['实际仓位变化'] < -threshold, '卖出', '持有')
    )

    trade_table = trade_df.loc[trade_df['实际仓位变化'].abs() > threshold].copy()
    state_map = {
        'bull': '多头主导',
        'range': '震荡主导',
        'bear': '空头主导',
        'warmup': '预热期',
    }
    trade_table['市场状态'] = trade_table['dominant_state'].map(state_map).fillna('未知')
    trade_table = trade_table.sort_values('日期', ascending=False).head(200)
    trade_table['日期'] = trade_table['日期'].dt.strftime('%Y-%m-%d')

    display_cols = [
        '日期', '交易方向', '市场状态', '收盘价',
        '当日实际仓位', '实际仓位变化'
    ]

    if not trade_table.empty:
        st.caption(f"交易明细条数: {len(trade_table)}（按日期倒序，最多200行）")
        def highlight_status(val):
            if val == '多头主导':
                return 'color: #d62728; font-weight: 700;'
            if val == '空头主导':
                return 'color: #2ca02c; font-weight: 700;'
            if val == '震荡主导':
                return 'color: #1f77b4; font-weight: 700;'
            return 'color: #888;'

        st.dataframe(
            trade_table[display_cols].style
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', '700')]}
            ], overwrite=False)
            .set_properties(**{'text-align': 'center'})
            .format({'收盘价': '{:.2f}'})
            .format('{:.2%}', subset=['当日实际仓位', '实际仓位变化'])
            .map(highlight_status, subset=['市场状态']),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("当前区间无实际调仓交易")

    # ========== 页脚 ==========
    st.divider()
    st.caption(
        "OPT Convex 策略 | V5.2 | 开发: Mars Yuan"
    )


if __name__ == '__main__':
    main()
