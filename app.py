
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Global Poverty Rankings", layout="wide")

st.title("이 세상 국가들의 빈곤 순위 — 선 그래프 시각화")
st.caption("데이터: 월드뱅크 국제 빈곤선(하루 $2.15) 지표 • 실패 시 로컬 샘플 사용")

@st.cache_data(show_spinner=False)
def load_sample():
    path = "data/sample_poverty_215.csv"
    df = pd.read_csv(path)
    return df

@st.cache_data(show_spinner=True, ttl=60*60)
def fetch_worldbank():
    """World Bank API에서 국제 빈곤선($2.15/day) 지표(SI.POV.DDAY)를 불러오고 가공.
    실패 시 None 반환."""
    try:
        # 큰 페이지 수로 한 번에 받아오기
        url = "https://api.worldbank.org/v2/country/all/indicator/SI.POV.DDAY?format=json&per_page=20000"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or len(data) < 2:
            return None
        rows = []
        for item in data[1]:
            # item keys: country, countryiso3code, date, value, unit, obs_status, decimal
            ctry = item.get("country", {}).get("value")
            iso3 = item.get("countryiso3code")
            year = item.get("date")
            val = item.get("value")
            if ctry and iso3 and year and val is not None:
                rows.append((int(year), ctry, iso3, float(val)))
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["Year", "Country", "ISO3", "Headcount215"])
        # 최신년도를 우선으로 하고 결측/중복 정리
        df = df.dropna(subset=["Headcount215"])
        return df
    except Exception:
        return None

# 데이터 로딩: API 우선 -> 실패 시 샘플
df_api = fetch_worldbank()
if df_api is not None:
    df = df_api
    st.success("월드뱅크 API 로딩 성공 (SI.POV.DDAY).")
else:
    df = load_sample()
    st.warning("API 로딩 실패. 로컬 샘플 데이터를 사용합니다.")

# 연도 범위 및 국가 선택
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
with st.sidebar:
    st.header("필터")
    year_range = st.slider("연도 범위", min_value=min_year, max_value=max_year, value=(max(min_year, max_year-20), max_year))
    countries = st.multiselect(
        "국가 선택(여러 개 가능)",
        options=sorted(df["Country"].unique().tolist()),
        default=[c for c in ["Korea, Rep.", "United States", "India", "Nigeria", "Brazil"] if c in df["Country"].unique()]
    )
    y_mode = st.radio("Y축", options=["빈곤율(%)", "순위(연도별)"], index=1, horizontal=True)
    topn = st.number_input("연도별 Top N(가장 빈곤율 높은 국가)", min_value=3, max_value=50, value=10, step=1)

# 연도 범위 적용
df_year = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])].copy()

# 연도별 순위 계산 (빈곤율 높을수록 순위 1위)
def add_rank_per_year(dfin):
    dfin = dfin.copy()
    dfin["Rank"] = dfin.groupby("Year")["Headcount215"].rank(method="dense", ascending=False).astype(int)
    return dfin
df_year = add_rank_per_year(df_year)

# 상단 KPI: 선택 연도의 Top N 미리보기
st.subheader("연도별 Top N 미리보기")
col1, col2 = st.columns(2)
with col1:
    target_year = int(df_year["Year"].max())
    st.write(f"가장 최신 연도 Top {topn} (연도: {target_year}) — 빈곤율(%) 기준")
    latest = df_year[df_year["Year"] == target_year].sort_values("Headcount215", ascending=False).head(int(topn))
    st.dataframe(latest[["Country", "ISO3", "Year", "Headcount215", "Rank"]].reset_index(drop=True), use_container_width=True)
with col2:
    target_year2 = int(df_year["Year"].min())
    st.write(f"선택 구간 시작 연도 Top {topn} (연도: {target_year2}) — 빈곤율(%) 기준")
    earliest = df_year[df_year["Year"] == target_year2].sort_values("Headcount215", ascending=False).head(int(topn))
    st.dataframe(earliest[["Country", "ISO3", "Year", "Headcount215", "Rank"]].reset_index(drop=True), use_container_width=True)

# 라인 그래프: 선택 국가만
if not countries:
    st.info("왼쪽에서 최소 1개 이상의 국가를 선택하세요.")
    st.stop()

plot_df = df_year[df_year["Country"].isin(countries)].copy()

if y_mode == "빈곤율(%)":
    fig = px.line(
        plot_df.sort_values(["Country", "Year"]),
        x="Year", y="Headcount215", color="Country",
        markers=True,
        labels={"Headcount215": "빈곤율(%)"},
        title="국가별 국제 빈곤선($2.15/일) 빈곤율 추이"
    )
    fig.update_layout(yaxis_title="빈곤율(%)", xaxis_title="연도", legend_title="국가")
    st.plotly_chart(fig, use_container_width=True)
else:
    # 순위가 낮을수록(숫자 작을수록) 더 빈곤함을 의미하므로 y축 역전
    fig = px.line(
        plot_df.sort_values(["Country", "Year"]),
        x="Year", y="Rank", color="Country",
        markers=True,
        labels={"Rank": "순위(연도별)"},
        title="국가별 빈곤 순위 추이 (연도별 빈곤율 높은 순)"
    )
    fig.update_layout(yaxis_title="순위(작을수록 빈곤율 높음)", xaxis_title="연도", legend_title="국가", yaxis_autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown("""
**해석 가이드**
- 지표는 국제 빈곤선($2.15/일) 기준 빈곤 **비율(%)** 입니다. (World Bank `SI.POV.DDAY`)
- '순위'는 **해당 연도에 빈곤율이 높은 국가일수록 더 작은 숫자(1위)** 를 부여해 만든 것입니다.
- 국가·연도별 결측이 존재할 수 있으니, 비교 시 같은 연도 범위에서 보세요.
""")
