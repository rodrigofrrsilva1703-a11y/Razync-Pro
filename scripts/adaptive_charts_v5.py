from pathlib import Path

app_path = Path('app.py')
ui_path = Path('ui_system.py')

s = app_path.read_text(encoding='utf-8')
u = ui_path.read_text(encoding='utf-8')

# Replace every direct Plotly render with one central themed renderer.
s = s.replace('st.plotly_chart(', 'themed_plotly_chart(')

anchor = 'inject_design_system(UI_THEME)\n'
helper = '''\n\ndef themed_plotly_chart(fig, *args, **kwargs):\n    """Render any Plotly figure using the active Razync theme."""\n    apply_plot_theme(fig, UI_THEME)\n    config = kwargs.get("config") or {}\n    config.setdefault("displayModeBar", False)\n    config.setdefault("responsive", True)\n    kwargs["config"] = config\n    return st.plotly_chart(fig, *args, **kwargs)\n'''
if 'def themed_plotly_chart(' not in s:
    s = s.replace(anchor, anchor + helper, 1)

# Replace the theme function at the end of ui_system.py with a complete adaptive version.
start = u.index('def apply_plot_theme(')
new_func = '''def apply_plot_theme(fig, theme_name: str, *, height: int | None = None) -> None:\n    """Apply Razync theme tokens to the entire Plotly figure, including axes and hover UI."""\n    t = tokens(theme_name)\n    dark = theme_name == "Escuro"\n    grid = "#263750" if dark else "#e6edf5"\n    axis = "#52657f" if dark else "#cbd6e2"\n    hover_bg = "#1b2940" if dark else "#ffffff"\n    hover_text = "#edf3fb" if dark else "#334155"\n    hover_border = "#3a506f" if dark else "#d9e2ec"\n    colorway = [\n        t["primary"], t["success"], t["warning"], t["danger"],\n        "#9b8cf2" if dark else "#7c6fd1",\n        "#5bb7c7" if dark else "#4196a6",\n    ]\n    kwargs = {\n        "template": t["plot"],\n        "paper_bgcolor": "rgba(0,0,0,0)",\n        "plot_bgcolor": "rgba(0,0,0,0)",\n        "font": {"color": t["text"], "family": "Inter, system-ui, sans-serif"},\n        "margin": dict(l=8, r=8, t=18, b=8),\n        "legend_title_text": "",\n        "colorway": colorway,\n        "hoverlabel": dict(\n            bgcolor=hover_bg,\n            bordercolor=hover_border,\n            font=dict(color=hover_text, family="Inter, system-ui, sans-serif"),\n        ),\n    }\n    if height:\n        kwargs["height"] = height\n    fig.update_layout(**kwargs)\n    fig.update_xaxes(\n        showgrid=False, zeroline=False, linecolor=axis, tickcolor=axis,\n        tickfont=dict(color=t["muted"]), title_font=dict(color=t["muted"]),\n    )\n    fig.update_yaxes(\n        showgrid=True, gridcolor=grid, gridwidth=1, zeroline=False, linecolor=axis,\n        tickcolor=axis, tickfont=dict(color=t["muted"]), title_font=dict(color=t["muted"]),\n    )\n'''
u = u[:start] + new_func

app_path.write_text(s, encoding='utf-8')
ui_path.write_text(u, encoding='utf-8')
print('adaptive charts applied')
# trigger
