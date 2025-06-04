import pandas as pd
import numpy as np
import streamlit as st
from pyecharts.charts import Line, Bar, Pie, Timeline, HeatMap, Geo, Map
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode


# 页面设置
st.set_page_config(layout="wide", page_title="🦠 COVID-19 全球疫情分析可视化大屏")

# 数据加载与预处理
df = pd.read_csv("D:\Jupyter\covid_19_data.csv")
df.columns = [c.strip().replace("/", "_").replace(" ", "_") for c in df.columns]
df['ObservationDate'] = pd.to_datetime(df['ObservationDate'], errors='coerce')
df = df.dropna(subset=['ObservationDate', 'Country_Region'])
df['Country_Region'] = df['Country_Region'].replace({"Hong Kong": "China","Macau": "China","Taiwan": "China","Mainland China": "China"})
df['Province_State'] = df.apply(lambda row: "Unknown" if pd.isna(row['Province_State']) else row['Province_State'], axis=1)
df_grouped = df.groupby(['Country_Region', 'Province_State', 'ObservationDate'], as_index=False)[['Confirmed', 'Deaths', 'Recovered']].max()
# 全球统计
world_data = df.groupby(['Country_Region', 'ObservationDate'])[['Confirmed', 'Deaths', 'Recovered']].sum().reset_index()
data = pd.read_csv("D:/Jupyter/covid_19_data.csv")
data['Country/Region'] = data['Country/Region'].replace({"Hong Kong": "China","Macau": "China","Taiwan": "China","Mainland China": "China","US": "United States","UK": "United Kingdom"})
country_data = data.groupby('Country/Region')['Confirmed'].sum().reset_index()

# 国家选择器
all_countries = sorted(df_grouped['Country_Region'].unique().tolist())
country = st.sidebar.selectbox("🌍 选择国家/地区", ["All"] + all_countries)

if country != "All":
    country_df = df_grouped[df_grouped['Country_Region'] == country]
    summary = country_df.groupby('ObservationDate')[['Confirmed', 'Deaths', 'Recovered']].sum().reset_index()
else:
    country_df = world_data.copy()
    summary = world_data.groupby('ObservationDate')[['Confirmed', 'Deaths', 'Recovered']].sum().reset_index()
if country == "China":
    # 中文省份映射
    en2zh = {
        "Anhui": "安徽", "Beijing": "北京", "Chongqing": "重庆", "Fujian": "福建",
        "Gansu": "甘肃", "Guangdong": "广东", "Guangxi": "广西", "Guizhou": "贵州",
        "Hainan": "海南", "Hebei": "河北", "Heilongjiang": "黑龙江", "Henan": "河南",
        "Hubei": "湖北", "Hunan": "湖南", "Inner Mongolia": "内蒙古", "Jiangsu": "江苏",
        "Jiangxi": "江西", "Jilin": "吉林", "Liaoning": "辽宁", "Ningxia": "宁夏",
        "Qinghai": "青海", "Shaanxi": "陕西", "Shandong": "山东", "Shanghai": "上海",
        "Shanxi": "山西", "Sichuan": "四川", "Tianjin": "天津", "Tibet": "西藏",
        "Xinjiang": "新疆", "Yunnan": "云南", "Zhejiang": "浙江", "Hong Kong": "香港",
        "Macau": "澳门", "Taiwan": "台湾","China": "中国"
    }
    # 英文省份转换为中文名
    country_df.loc[:, 'Country_Region'] = country_df['Country_Region'].map(en2zh)
    country_df.loc[:, 'Province_State'] = country_df['Province_State'].map(en2zh)

    country = "中国"
    # country_df = country_df[country_df['Province_State'] != "未知"]

# 日期和省份列表
dates = sorted(country_df['ObservationDate'].dt.strftime("%Y-%m-%d").unique().tolist())
# provinces = sorted(country_df['Province_State'].unique().tolist())

# 图表函数
def render(chart, height=600, width=800):
    # 添加CSS样式，使图表居中
    html_str = f"""
    <div style="display: flex; justify-content: center; align-items: center; height: {height}px; width: {width}px;">
        {chart.render_embed()}
    </div>
    """
    return st.components.v1.html(html_str, height=height, width=width)
def renders(chart, height=600, width=800):
    return st.components.v1.html(chart.render_embed(), height=height, width=width)

def geo_map():
    latest_data = country_df[country_df['ObservationDate'] == country_df['ObservationDate'].max()]
    data_pair = latest_data.groupby('Province_State')['Confirmed'].sum().reset_index().values.tolist()
    return Geo(init_opts=opts.InitOpts(width='2350px', height='1100px'))\
        .add_schema(maptype="china")\
        .add("确诊人数", data_pair)\
        .set_series_opts(
            label_opts=opts.LabelOpts(
                is_show=True,
                formatter="{b}",
                position="right"
            )
        )\
        .set_global_opts(
            title_opts=opts.TitleOpts(title=""),
            visualmap_opts=opts.VisualMapOpts(max_=max([x[1] for x in data_pair]))
        )


def map_globe():
    return Map(init_opts=opts.InitOpts(width='2400px', height='1200px'))\
        .add("累计确诊病例", [list(z) for z in zip(country_data['Country/Region'], country_data['Confirmed'])], "world")\
        .set_global_opts(title_opts=opts.TitleOpts(title=""),legend_opts=opts.LegendOpts(is_show=False),
                         visualmap_opts=opts.VisualMapOpts(max_=int(country_data['Confirmed'].max())))

def map_country():
    selected_value = country_data[country_data['Country/Region'] == country]['Confirmed'].sum()
    return Map(init_opts=opts.InitOpts(width='1400px', height='600px'))\
        .add("累计确诊病例", [[country, selected_value]], "world")\
        .set_global_opts(title_opts=opts.TitleOpts(title=""),legend_opts=opts.LegendOpts(is_show=False),
                         visualmap_opts=opts.VisualMapOpts(max_=int(country_data['Confirmed'].max())))

def line_chart(width='2350px', height='1100px'):
    return Line(init_opts=opts.InitOpts(width=width, height=height))\
        .add_xaxis(summary['ObservationDate'].dt.strftime("%Y-%m-%d").tolist())\
        .add_yaxis("累计确诊", summary['Confirmed'].tolist(), is_smooth=True)\
        .add_yaxis("累计死亡", summary['Deaths'].tolist(), is_smooth=True)\
        .add_yaxis("累计治愈", summary['Recovered'].tolist(), is_smooth=True)\
        .set_global_opts(title_opts=opts.TitleOpts(title=""),
                         tooltip_opts=opts.TooltipOpts(trigger="axis"),datazoom_opts=[
            opts.DataZoomOpts(type_="slider", orient="horizontal", range_start=0, range_end=100),
        ],yaxis_opts=opts.AxisOpts(
                name="人数",
                axislabel_opts=opts.LabelOpts(formatter=JsCode("function(x){return x >= 10000 ? (x / 10000).toFixed(0) + '万' : x}"))
        ))

def bar_province(width='2350px', height='1100px'):
    latest = country_df[country_df['ObservationDate'] == country_df['ObservationDate'].max()]
    group_col = 'Province_State' if country != "All" else 'Country_Region'
    grouped = latest.groupby(group_col)[['Confirmed', 'Deaths', 'Recovered']].sum().sort_values("Confirmed",ascending=False).head(10)
    return Bar(init_opts=opts.InitOpts(width=width, height=height)).add_xaxis(grouped.index.tolist()) \
        .add_yaxis("确诊", grouped['Confirmed'].tolist()) \
        .add_yaxis("死亡", grouped['Deaths'].tolist()) \
        .add_yaxis("治愈", grouped['Recovered'].tolist()) \
        .set_global_opts(title_opts=opts.TitleOpts(title=""),datazoom_opts=[
            opts.DataZoomOpts(type_="slider", orient="horizontal", range_start=0, range_end=100),
        ],yaxis_opts=opts.AxisOpts(
                name="人数",
                axislabel_opts=opts.LabelOpts(formatter=JsCode("function(x){return x >= 10000 ? (x / 10000).toFixed(1) + '万' : x}"))
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"))

def pie_latest(width='2350px', height='1100px'):
    latest = summary.iloc[-1]
    return Pie(init_opts=opts.InitOpts(width=width, height=height))\
        .add("", [["确诊", int(latest['Confirmed'])], ["死亡", int(latest['Deaths'])], ["治愈", int(latest['Recovered'])]],
             radius=["40%", "70%"],start_angle=20)\
        .set_global_opts(title_opts=opts.TitleOpts(title=""))\
        .set_series_opts(label_opts=opts.LabelOpts(formatter=JsCode("""
        function(params) {
            let value = params.value;
            let valStr = value >= 10000 ? (value / 10000).toFixed(1) + '万' : value;
            return params.name + ': ' + valStr + ' (' + params.percent + '%)';
        }
    """)))

def timeline_chart(width='2350px', height='1100px'):
    timeline = Timeline(init_opts=opts.InitOpts(width=width, height=height))
    for date in country_df['ObservationDate'].sort_values().unique()[0:365]:
        day_data = country_df[country_df['ObservationDate'] == date]
        group_col = 'Province_State' if country != "All" else 'Country_Region'
        top_group = day_data.groupby(group_col)["Confirmed"].sum().sort_values(ascending=False).head(10)
        chart = Bar().add_xaxis(top_group.index.astype(str).tolist()).add_yaxis("确诊", top_group.values.tolist())
        chart.set_global_opts(title_opts=opts.TitleOpts(title=""))
        timeline.add(chart, time_point=str(date.date()))
    return timeline

# 💠 仪表盘顶部数据区（如“累计确诊、死亡、治愈、死亡率”等）
st.markdown("<h2 style='text-align: center;'>🧾 疫情概览</h2>", unsafe_allow_html=True)

confirmed = int(summary['Confirmed'].max())
deaths = int(summary['Deaths'].max())
recovered = int(summary['Recovered'].max())
death_rate = f"{(deaths / confirmed * 100):.2f}%" if confirmed else "0.00%"
recovery_rate = f"{(recovered / confirmed * 100):.2f}%" if confirmed else "0.00%"

# 创建三列并显示
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🦠 累计确诊", f"{confirmed:,}")
col2.metric("💀 累计死亡", f"{deaths:,}")
col3.metric("💪 累计治愈", f"{recovered:,}")
col4.metric("📉 病死率", death_rate)
col5.metric("📈 治愈率", recovery_rate)
if country != "All":
    tabs = st.tabs(["🎛️ 图表总集","🎯 中国新冠地图" if country == "中国" else f"🌐 {country}新冠全球地图", "📈 疫情发展趋势", "🥧 病例情况占比", "🎞️ 省份确诊变化(一年)", "📊 各省病例情况"])
else:
    tabs = st.tabs(["🎛️ 图表总集","🌐 全球新冠地图", "📈 疫情发展趋势", "🥧 病例情况占比", "🎞️ 国家确诊变化(一年)", "📊 各国病例情况"])
with tabs[0]:
    # 图表排布
    charts = [
        ("📈 疫情发展趋势", line_chart, 400, 650),
        ("📊 各省病例情况" if country != "All" else "📊 各国病例情况", bar_province, 450, 650),
        ("🥧 病例情况占比", pie_latest, 450, 650),
        ("️🎞️ 省份确诊变化(一周)" if country != "All" else "🎞️ 国家确诊变化(一年)", timeline_chart, 450, 650),
    ]
    # 展示图表
    if country != "All":
        render(geo_map() if country == "中国" else map_country(),600,2400)
    else:
        renders(map_globe(),600,2400)
    cols = st.columns(4)
    for i, (title, chart_func, h, w) in enumerate(charts):
        with cols[i % 4]:
            renders(chart_func('600px','400px'), height=h, width=w)
with tabs[1]:
    if country != "All":
        st.markdown("<h3 style='text-align: center;'>🎯 中国各省新冠地图</h3>" if country == "中国" else f"<h3 style='text-align: center;'>🌐 {country}新冠全球地图</h3>", unsafe_allow_html=True)
        render(geo_map() if country == "中国" else map_country(),1200,2400)
    else:
        st.markdown("<h3 style='text-align: center;'>🌐 全球新冠地图</h3>",unsafe_allow_html=True)
        render(map_globe(),1200,2400)
with tabs[2]:
    st.markdown("<h3 style='text-align: center;'>📈 疫情发展趋势</h3>", unsafe_allow_html=True)
    render(line_chart(), 1200, 2400)
with tabs[3]:
    st.markdown("<h3 style='text-align: center;'>🥧 病例情况占比</h3>", unsafe_allow_html=True)
    render(pie_latest(), 1200, 2400)
with tabs[4]:
    if country != "All":
        st.markdown("<h3 style='text-align: center;'>🎞️ 省份确诊变化(一年)</h3>", unsafe_allow_html=True)
        render(timeline_chart(), 1200, 2400)
    else:
        st.markdown("<h3 style='text-align: center;'>🎞️ 国家确诊变化(一年)</h3>",unsafe_allow_html=True)
        render(timeline_chart(),1200,2400)
with tabs[5]:
    if country != "All":
        st.markdown("<h3 style='text-align: center;'>📊 各省病例情况</h3>", unsafe_allow_html=True)
        render(bar_province(), 1200, 2400)
    else:
        st.markdown("<h3 style='text-align: center;'>📊 各国病例情况</h3>",unsafe_allow_html=True)
        render(bar_province(),1200,2400)

# def heat_chart():
#     heat_data = []
#     for d in dates[0:7]:
#         for p in provinces:
#             val = country_df[(country_df['ObservationDate'].dt.strftime("%Y-%m-%d") == d) &
#                              (country_df['Province_State'] == p)]['Recovered'].sum()
#             heat_data.append([p, d, val])
#     return HeatMap(init_opts=opts.InitOpts(width='2350px', height='1100px'))\
#         .add_xaxis(dates[0:7])\
#         .add_yaxis("省份", provinces, [[d[1], d[0], d[2]] for d in heat_data])\
#         .set_global_opts(
#             title_opts=opts.TitleOpts(title="各省一周恢复热力图"),
#             visualmap_opts=opts.VisualMapOpts(min_=0, max_=max(d[2] for d in heat_data), orient="horizontal"))
# ("🔥 各省一周恢复热力图", heat_chart, 500, 700)
# import pandas as pd
# import streamlit as st
# from pyecharts.charts import Line, Bar, Pie, Timeline
# from pyecharts import options as opts
# from pyecharts.globals import ThemeType
#
# # 页面设置
# st.set_page_config(layout="wide", page_title="COVID-19 全球疫情可视化大屏")
# st.title("🦠 COVID-19 全球疫情可视化分析系统")
#
# # 数据加载与预处理
# df = pd.read_csv("D:\Jupyter\covid_19_data.csv")
# df.columns = [c.strip().replace("/", "_").replace(" ", "_") for c in df.columns]  # 清洗列名
#
# # 日期标准化并清洗缺失
# df['ObservationDate'] = pd.to_datetime(df['ObservationDate'], errors='coerce')
# df = df.dropna(subset=['ObservationDate', 'Country_Region'])
#
# df['Country_Region'] = df['Country_Region'].replace({"Mainland China": "China"})
#
# # 将空的省份填为 "(All)" 表示全国统计
# df['Province_State'] = df['Province_State'].fillna("(All)")
#
# # 聚合重复记录（使用最大值确保数据不为0）
# df_grouped = df.groupby(['Country_Region', 'Province_State', 'ObservationDate'], as_index=False)[['Confirmed', 'Deaths', 'Recovered']].max()
#
# # 国家选择器
# available_countries = df_grouped['Country_Region'].unique().tolist()
# country = st.sidebar.selectbox("🌍 选择国家/地区", sorted(available_countries))
#
# # 获取目标国家数据
# country_df = df_grouped[df_grouped['Country_Region'] == country].copy()
#
# # 日期汇总趋势
# summary = country_df.groupby('ObservationDate')[['Confirmed', 'Deaths', 'Recovered']].sum().reset_index()
#
# # 图1：时间趋势折线图
# line = (
#     Line(init_opts=opts.InitOpts(theme=ThemeType.MACARONS, width="1000px", height="500px"))
#     .add_xaxis(summary['ObservationDate'].dt.strftime("%Y-%m-%d").tolist())
#     .add_yaxis("累计确诊", summary['Confirmed'].tolist(), is_smooth=True)
#     .add_yaxis("累计死亡", summary['Deaths'].tolist(), is_smooth=True)
#     .add_yaxis("累计治愈", summary['Recovered'].tolist(), is_smooth=True)
#     .set_global_opts(
#         title_opts=opts.TitleOpts(title=f"{country} 疫情时间趋势"),
#         tooltip_opts=opts.TooltipOpts(trigger="axis"),
#         datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],
#         xaxis_opts=opts.AxisOpts(name="日期"),
#         yaxis_opts=opts.AxisOpts(name="病例数")
#     )
# )
# st.subheader("📈 疫情发展趋势")
# st.components.v1.html(line.render_embed(), height=550)
#
# # 图2：省/州累计分布柱状图（只选最后一天）
# latest_date = country_df['ObservationDate'].max()
# latest_data = country_df[country_df['ObservationDate'] == latest_date]
# prov_group = latest_data.groupby("Province_State")[["Confirmed", "Deaths", "Recovered"]].sum().sort_values("Confirmed", ascending=False).head(10)
#
# bar = (
#     Bar(init_opts=opts.InitOpts(theme=ThemeType.CHALK, width="1000px", height="500px"))
#     .add_xaxis(prov_group.index.tolist())
#     .add_yaxis("确诊", prov_group['Confirmed'].tolist())
#     .add_yaxis("死亡", prov_group['Deaths'].tolist())
#     .add_yaxis("治愈", prov_group['Recovered'].tolist())
#     .set_global_opts(title_opts=opts.TitleOpts(title=f"{country} 各省疫情概况 Top 10"))
# )
# st.subheader("📊 省级分布对比")
# st.components.v1.html(bar.render_embed(), height=550)
#
# # 图3：最新饼图占比
# latest_total = summary.iloc[-1]
# pie = (
#     Pie(init_opts=opts.InitOpts(theme=ThemeType.ROMA, width="700px", height="400px"))
#     .add("疫情比例", [
#         ["确诊", int(latest_total['Confirmed'])],
#         ["死亡", int(latest_total['Deaths'])],
#         ["治愈", int(latest_total['Recovered'])]
#     ], radius=["40%", "70%"])
#     .set_global_opts(title_opts=opts.TitleOpts(title=f"{country} 最新疫情占比"))
#     .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"))
# )
# st.subheader("🍰 最新疫情占比")
# st.components.v1.html(pie.render_embed(), height=460)
#
# # 图4：Timeline 动态柱图（最近10天）
# timeline = Timeline()
# last_10_days = country_df['ObservationDate'].sort_values().unique()[-10:]
# for date in last_10_days:
#     day_data = country_df[country_df['ObservationDate'] == date]
#     top_prov = day_data.groupby("Province_State")["Confirmed"].sum().sort_values(ascending=False).head(5)
#     chart = Bar().add_xaxis(top_prov.index.astype(str).tolist()).add_yaxis("确诊", top_prov.values.tolist())
#     chart.set_global_opts(title_opts=opts.TitleOpts(title=f"{country} 省份确诊前五 - {pd.to_datetime(date).date()}"))
#     timeline.add(chart, time_point=str(pd.to_datetime(date).date()))
#
# st.subheader("🎞️ 时间演变 - 省份确诊对比")
# st.components.v1.html(timeline.render_embed(), height=500)
