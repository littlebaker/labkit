from typing import Callable, List, Dict, Optional
from nicegui import ui


class SelectableTable:
    """
    轻量封装：
      1) 点击行选中；2) ArrowUp/ArrowDown 键移动选中；3) 选中行高亮。
    要求：rows 非空；row_key 为行内存在的字段名。
    """

    def __init__(self,
                 columns: List[Dict],
                 rows: List[Dict],
                 row_key: str,
                 on_change: Optional[Callable[[int, Dict], None]] = None,
                 height: int = 420) -> None:
        self.columns = columns
        self.rows = rows
        self.row_key = row_key
        self.on_change = on_change
        self.selected_index = 0

        self.container = ui.element('div').props('tabindex=0').classes('outline-none')
        with self.container:
            self.table = ui.table(
                title='',
                columns=self.columns,
                rows=self.rows,
                row_key=self.row_key,
                selection='single',
                on_select=self._on_select,
                pagination={'rowsPerPage': 0},
            ).classes('w-full')
            self.table.props(f'virtual-scroll style="max-height:{height}px" dense')
            self.table.selected = [self.get_selected_row()]

        self.container.on('keydown', self._on_key)
        self.container.on('click', lambda: self.container.run_method('focus'))
        self._emit_change()

    def get_selected_index(self) -> int:
        return self.selected_index

    def get_selected_row(self) -> Dict:
        return self.rows[self.selected_index]

    def set_selected_index(self, idx: int) -> None:
        idx = max(0, min(idx, len(self.rows) - 1))
        if idx != self.selected_index:
            self.selected_index = idx
            self.table.selected = [self.get_selected_row()]
            self.table.update()
            self._emit_change()

    def update_rows(self, new_rows: List[Dict]) -> None:
        old_row = self.get_selected_row()
        self.rows[:] = new_rows
        k = old_row[self.row_key]
        self.selected_index = next(i for i, r in enumerate(new_rows) if r[self.row_key] == k)
        self.table.rows = new_rows
        self.table.selected = [self.get_selected_row()]
        self.table.update()
        self._emit_change()

    def _on_select(self, e) -> None:
        row = e.selection[0]
        self.selected_index = self.rows.index(row)
        self._emit_change()

    def _on_key(self, e) -> None:
        self.table.run_method("function{console.log(123)}()")
        key = e.args['key']
        if key == 'ArrowUp':
            self.set_selected_index(self.selected_index - 1)
        elif key == 'ArrowDown':
            self.set_selected_index(self.selected_index + 1)

    def _emit_change(self) -> None:
        if self.on_change:
            self.on_change(self.selected_index, self.get_selected_row())

# ------------------- DEMO -------------------
demo_columns = [
    {'name': 'id', 'label': 'ID', 'field': 'id'},
    {'name': 'name', 'label': 'Name', 'field': 'name'},
    {'name': 'score', 'label': 'Score', 'field': 'score'},
]
demo_rows = [
    {'id': 1, 'name': 'Alice', 'score': 93},
    {'id': 2, 'name': 'Bob', 'score': 88},
    {'id': 3, 'name': 'Carol', 'score': 75},
    {'id': 4, 'name': 'Dave', 'score': 98},
    {'id': 5, 'name': 'Eve', 'score': 85},
    {'id': 6, 'name': 'Frank', 'score': 91},
    {'id': 7, 'name': 'Grace', 'score': 78},
    {'id': 8, 'name': 'Hank', 'score': 95},
    {'id': 9, 'name': 'Ivy', 'score': 82},
    {'id': 10, 'name': 'Jack', 'score': 97},
    {'id': 11, 'name': 'Kate', 'score': 89},
    {'id': 12, 'name': 'Liam', 'score': 92},
    {'id': 13, 'name': 'Mia', 'score': 84},
    {'id': 14, 'name': 'Nathan', 'score': 96},
    {'id': 15, 'name': 'Olivia', 'score': 87},
    {'id': 16, 'name': 'Peter', 'score': 90},
    {'id': 17, 'name': 'Quinn', 'score': 83},
    {'id': 18, 'name': 'Ryan', 'score': 94},
    {'id': 19, 'name': 'Sophia', 'score': 86},
    {'id': 20, 'name': 'Thomas', 'score': 99},
    {'id': 21, 'name': 'Uma', 'score': 81},
    {'id': 22, 'name': 'Victor', 'score': 93},
    {'id': 23, 'name': 'Wendy', 'score': 88},
    {'id': 24, 'name': 'Xavier', 'score': 95},
    {'id': 25, 'name': 'Yara', 'score': 82},
    {'id': 26, 'name': 'Zane', 'score': 97},
    {'id': 27, 'name': 'Amy', 'score': 84},
    {'id': 28, 'name': 'Brian', 'score': 91},
    {'id': 29, 'name': 'Cindy', 'score': 78},
]

@ui.page('/')
def main_page(client):
    ui.label('CONTENT')
    [ui.label(f'Line {i}') for i in range(100)]
    with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        ui.label('HEADER')
        # ui.button(on_click=lambda: right_drawer.toggle(), icon='menu').props('flat color=white')
    with ui.left_drawer(top_corner=True, bottom_corner=True).style('background-color: #d7e3f4'):
        ui.label('LEFT DRAWER')
    # with ui.right_drawer(fixed=False).style('background-color: #ebf1fa').props('bordered') as right_drawer:
    #     ui.label('RIGHT DRAWER')
    # with ui.footer().style('background-color: #3874c8'):
    #     ui.label('FOOTER')

    ui.label('上下键移动选中；点击行也可以选择').classes('text-sm text-gray-600 mb-2')
    info = ui.label('').classes('mb-2')
    ui.table(rows=demo_rows, row_key='id').on("keydown", lambda e: print(e))

    def on_change(i, row):
        info.set_text(f'当前选中：index={i}, row={row}')

    with ui.left_drawer(top_corner=True, bottom_corner=True).style('background-color: #d7e3f4'):
        st = SelectableTable(demo_columns, demo_rows, row_key='id', on_change=on_change, height=320)

    # with ui.row().classes('mt-2 gap-2'):
    #     ui.button('上移', on_click=lambda: st.set_selected_index(st.get_selected_index()-1))
    #     ui.button('下移', on_click=lambda: st.set_selected_index(st.get_selected_index()+1))

ui.run(native=False, reload=False)
