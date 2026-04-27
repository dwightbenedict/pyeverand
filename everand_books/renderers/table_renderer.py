from lxml.etree import Element

from everand_books.normalization.tables import TableBlock
from everand_books.renderers.renderer import E, register_renderer, render


@register_renderer("table")
def render_table(block: TableBlock) -> Element:
    table = E.table()

    for row in block.rows:
        tr = E.tr()

        for cell in row.cells:
            td = E.td(style=cell.style)

            for node in cell.nodes:
                td.append(render(node))

            tr.append(td)

        table.append(tr)

    return E.div(table)