import streamlit as st
import glob
import numpy as np
import pandas as pd
from pathlib import Path

from labkit.visualizations.adapters.quantify_adapter import draw_figure, get_all_runs, parse_run, get_dataset, get_metadata
from labkit.visualizations.scroll_manager import init_scroll_management, preserve_scroll_position, restore_scroll_position

# 初始化滚动管理
init_scroll_management()

base_dir = Path("/home/machine4/LSY_NEW/quantify-data")

experiments = [x for x in base_dir.iterdir() if (x.is_dir() and not x.name.startswith("."))]

run_selector = st.sidebar.selectbox(
    "Select folder", [x.name for x in experiments]
)

# 根据选择的结果获取对应的experiments里的path
if run_selector:
    # 找到选中的实验文件夹
    selected_experiment = None
    for exp in experiments:
        if exp.name == run_selector:
            selected_experiment = exp
            break
    
    if selected_experiment:
        experiment_path = selected_experiment
        st.write(f"Selected experiment path: {experiment_path.name}")
        
        # 显示实验文件夹中的内容
        # st.write("Experiment contents:")
        # for item in experiment_path.iterdir():
        #     st.write(f"- {item.name} ({'Directory' if item.is_dir() else 'File'})")
    else:
        st.error("Selected experiment not found!")


all_runs = get_all_runs(experiment_path)



# 使用parse_run处理所有run
run_infos = []
for run_path in all_runs:
    try:
        info = parse_run(run_path)
        info["run_path"] = str(run_path)
        run_infos.append(info)
    except Exception as e:
        # 跳过无法解析的run
        continue

run_infos = sorted(run_infos, key=lambda x: x["time"])

event = None
if run_infos:
    # 构建DataFrame
    df = pd.DataFrame(run_infos)
    # 调整列顺序（保留 run_path 供选择映射，但在表格中隐藏）
    columns = ["time", "run_name", "random", "run_path"]
    # 将time列转换为更易读的字符串格式，并加上上午/下午
    def format_time_with_ampm(dt):
        hour = dt.hour
        if hour < 12:
            ampm = "上午"
        else:
            ampm = "下午"
        return dt.strftime(f"%Y-%m-%d {ampm} %H:%M:%S")
    df["time"] = df["time"].apply(format_time_with_ampm)
    df = df[columns]
    # 显示表格（不展示 run_path 列，选中后用行号映射到原数据获取路径）
    
    key = "runs_table"
    df_visible = df[["time", "run_name", "random"]]

    st.sidebar.divider()
    st.sidebar.write("所有run信息：")
    
    # 在表格显示前标记滚动位置
    if len(df_visible) > 0:
        preserve_scroll_position("runs_table")
    
    event = st.sidebar.dataframe(
        df_visible,
        hide_index=True,
        key=key,
        # use_container_width=True,
        selection_mode="single-cell",
        on_select="rerun"
    )
    
    # # 如果有选择，在交互后恢复滚动位置
    # if event.selection.cells:
    #     restore_scroll_position()





else:
    st.write("没有可用的run信息。")


# 如果有选中，则显示选中的run信息
selected_run_path: Path = None
if event is not None and len(event.selection.cells) > 0:
    selected_idx = event.selection.cells[0][0]
    selected_run_path = all_runs[selected_idx]


if selected_run_path:
    # st.write(f"已选择的 run 路径：{selected_run_path}")


    # st.divider()

    if (selected_run_path / 'dataset.hdf5').exists():
        cols = st.columns(2)
        dataset = get_dataset(selected_run_path)
        # st.write(dataset)
        metadata = get_metadata(selected_run_path)
        # st.json(metadata)

        fig_type = st.selectbox("Figure类型：", ['amp', 'phase', 'original'])
        
        # # 在显示图表前标记滚动位置
        # preserve_scroll_position("charts_section")

        figs = [cols[i % 2].plotly_chart(x) for i, x in enumerate(draw_figure(dataset, fig_type))]
        
        # # 图表显示完成后恢复滚动位置
        # restore_scroll_position()
        # print(figs)
    else:
        st.error("该run目录下没有dataset.hdf5文件")
        st.write([x.name for x in selected_run_path.iterdir()])

st.divider()
# 显示其他图片：
if selected_run_path:
    st.write("其他图片：")
    glob_path = selected_run_path / "*.*"
    for path in glob.glob(glob_path.as_posix()):
        st.text(path)