from pathlib import Path
from importlib import import_module
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"cash": 1000.0, "positions": {}, "trade_history": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"cash": 1000.0, "positions": {}, "trade_history": []}
    return data


def main() -> None:
    pd = import_module("pandas")
    px = import_module("plotly.express")
    st = import_module("streamlit")
    WorldModel = import_module("lifeforce.memory.world_model").WorldModel

    st.set_page_config(page_title="Lifeforce Trading Dashboard", layout="wide")
    st.title("Lifeforce 交易生存实验看板")
    state_path = Path(".lifeforce/trading/simulator_state.json")
    state = load_state(state_path)
    world_model = WorldModel()

    cash = float(state.get("cash", 0.0))
    positions = state.get("positions", {})
    history = state.get("trade_history", [])

    col1, col2, col3 = st.columns(3)
    col1.metric("账户现金", f"${cash:,.2f}")
    col2.metric("持仓数量", len(positions))
    col3.metric("交易次数", len(history))

    st.subheader("持仓列表")
    if positions:
        pos_df = pd.DataFrame(
            [{"symbol": symbol, "amount": data.get("amount", 0), "entry_price": data.get("entry_price", 0)} for symbol, data in positions.items()]
        )
        st.dataframe(pos_df, use_container_width=True)
    else:
        st.info("当前无持仓")

    st.subheader("交易历史")
    if history:
        trades_df = pd.DataFrame(history)
        st.dataframe(trades_df.tail(50), use_container_width=True)
        if "timestamp" in trades_df.columns and "cash_after" in trades_df.columns:
            chart_df = trades_df.copy()
            chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
            fig = px.line(chart_df, x="timestamp", y="cash_after", title="资金曲线")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无交易历史")

    st.subheader("世界模型洞察")
    st.text(world_model.get_summary())


if __name__ == "__main__":
    main()
