"""
Streamlit 滚动位置管理器
基于 session_state 记录当前位置并使用 JavaScript 恢复
"""

import streamlit as st
import streamlit.components.v1 as components
import time
import hashlib


def init_scroll_management():
    """初始化滚动管理"""
    if 'current_section_id' not in st.session_state:
        st.session_state.current_section_id = None
    if 'section_counter' not in st.session_state:
        st.session_state.section_counter = 0


def start_scroll_section(section_name: str = None):
    """开始一个新的滚动区域 - 在可能触发重新渲染的内容前调用
    
    Args:
        section_name: 区域名称，用于生成唯一ID
    
    Returns:
        section_id: 生成的区域ID
    """
    # 生成唯一的区域ID
    st.session_state.section_counter += 1
    if section_name:
        section_id = f"section-{section_name}-{st.session_state.section_counter}"
    else:
        section_id = f"section-{st.session_state.section_counter}"
    
    # 保存当前区域ID
    st.session_state.current_section_id = section_id
    
    # 创建区域标记
    st.markdown(f'<div id="{section_id}"></div>', unsafe_allow_html=True)
    
    return section_id


def end_scroll_section():
    """结束滚动区域 - 在内容渲染完成后调用，自动滚动到区域开始位置"""
    if st.session_state.current_section_id:
        # 使用时间戳强制JavaScript重新执行
        components.html(f'''
        <script>
            // Time of creation of this script = {time.time()}.
            // The time changes everytime and hence would force streamlit to execute JS function
            function scrollToMySection() {{
                var element = window.parent.document.getElementById("{st.session_state.current_section_id}");
                if (element) {{
                    element.scrollIntoView({{ behavior: "instant" }});
                }} else {{
                    setTimeout(scrollToMySection, 100);
                }}
            }}
            scrollToMySection();
        </script>
        ''', height=0)


def create_scroll_section(section_name: str = None):
    """创建一个完整的滚动区域管理器
    
    使用方法：
    with create_scroll_section("my_section"):
        # 你的内容
        st.write("内容")
    
    或者手动调用：
    section_id = create_scroll_section("my_section")
    # 你的内容
    # 内容结束后会自动滚动
    """
    return ScrollSection(section_name)


class ScrollSection:
    """滚动区域上下文管理器"""
    
    def __init__(self, section_name: str = None):
        self.section_name = section_name
        self.section_id = None
    
    def __enter__(self):
        self.section_id = start_scroll_section(self.section_name)
        return self.section_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_scroll_section()


# 简化的API函数
def preserve_scroll_position(section_name: str = None):
    """保持滚动位置的简化函数 - 在交互组件前调用"""
    return start_scroll_section(section_name)


def restore_scroll_position():
    """恢复滚动位置 - 在交互组件后调用"""
    end_scroll_section()
