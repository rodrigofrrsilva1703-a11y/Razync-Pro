from __future__ import annotations

from html import escape

import streamlit as st

# Shared light and dark palettes for the redesigned workspace.
THEMES = {
    "Claro": {
        "bg": "#f5f7f9",
        "surface": "#ffffff",
        "surface_soft": "#f0f5f5",
        "sidebar": "#ffffff",
        "text": "#172c35",
        "muted": "#627780",
        "border": "#e4ebed",
        "control_border": "#c5d4d8",
        "control_bg": "#f8fbfd",
        "primary": "#087f79",
        "primary_hover": "#066960",
        "primary_soft": "#e8f5ef",
        "success": "#16835f",
        "warning": "#a86b14",
        "danger": "#bc4855",
        "shadow": "0 8px 28px rgba(38, 63, 76, .055)",
        "shadow_soft": "0 2px 10px rgba(38, 63, 76, .04)",
        "plot": "plotly_white",
    },
    "Escuro": {
        "bg": "#0c161c",
        "surface": "#14232c",
        "surface_soft": "#1c3039",
        "sidebar": "#14232c",
        "text": "#edf5f6",
        "muted": "#a2b7c1",
        "border": "#2a404b",
        "control_border": "#385269",
        "control_bg": "#101d2a",
        "primary": "#5ad6c4",
        "primary_hover": "#80e5d5",
        "primary_soft": "#163d3b",
        "success": "#68d8ac",
        "warning": "#f0c074",
        "danger": "#ff9a9a",
        "shadow": "0 12px 34px rgba(0, 0, 0, .24)",
        "shadow_soft": "0 4px 16px rgba(0, 0, 0, .16)",
        "plot": "plotly_dark",
    },
}


def tokens(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES["Claro"])


def inject_design_system(theme_name: str) -> None:
    """Emit theme tokens; all workspace styling lives in workspace.css."""
    t = tokens(theme_name)
    names = {
        "bg": "bg", "surface": "surface", "soft": "surface_soft", "text": "text",
        "muted": "muted", "border": "border", "control-border": "control_border",
        "control-bg": "control_bg", "primary": "primary", "primary-soft": "primary_soft",
        "success": "success", "warning": "warning", "danger": "danger",
    }
    css = ":root {" + ";".join(f"--rz-{name}:{t[key]}" for name, key in names.items()) + ";}"
    st.markdown(
        "<style>" + css + '''
        #MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none; }
        [data-testid="stToolbar"] button:not([data-testid="stExpandSidebarButton"]) { display:none; }
        </style>''',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "Razync Pro • MEI") -> None:
    """Render a consistent, compact page context for every product area."""
    st.markdown(
        f'<div class="rz-eyebrow">{escape(eyebrow)}</div>'
        f'<h1 class="rz-page-title">{escape(title)}</h1>'
        f'<p class="rz-page-sub">{escape(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="rz-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="rz-section-sub">{subtitle}</div>', unsafe_allow_html=True)


def business_card(name: str, year: int, cnpj: str | None = None) -> None:
    meta = f"Ano {year}"
    if cnpj:
        meta += f" • CNPJ {cnpj}"
    st.markdown(
        f'<div class="rz-business"><div class="rz-business-name">{name}</div><div class="rz-business-meta">{meta} • visão consolidada financeira e fiscal</div></div>',
        unsafe_allow_html=True,
    )


def alert_card(level: str, title: str, text: str) -> None:
    cls = {"danger": "rz-danger", "warn": "rz-warn", "info": "rz-info", "ok": "rz-ok"}.get(level, "rz-info")
    st.markdown(
        f'<div class="rz-alert {cls}"><div class="rz-alert-title">{title}</div><div class="rz-alert-text">{text}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, text: str, icon: str = "○") -> None:
    st.markdown(
        f'<div class="rz-empty"><div class="rz-empty-icon">{icon}</div><div class="rz-empty-title">{title}</div><div class="rz-empty-text">{text}</div></div>',
        unsafe_allow_html=True,
    )


def helper_note(text: str) -> None:
    st.markdown(f'<div class="rz-helper">{text}</div>', unsafe_allow_html=True)


def apply_plot_theme(fig, theme_name: str, *, height: int | None = None) -> None:
    t = tokens(theme_name)
    dark = theme_name == "Escuro"
    grid = t["border"]
    axis = t["border"]
    hover_bg = t["surface"]
    hover_text = t["text"]
    hover_border = t["control_border"]
    colorway = [
        t["primary"],
        t["success"],
        t["warning"],
        t["danger"],
        "#8f83ea" if dark else "#7568cf",
        "#48aab9" if dark else "#3c92a0",
    ]
    kwargs = {
        "template": t["plot"],
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": t["text"], "family": "Inter, system-ui, sans-serif"},
        "margin": dict(l=8, r=8, t=18, b=8),
        "legend_title_text": "",
        "colorway": colorway,
        "hoverlabel": dict(
            bgcolor=hover_bg,
            bordercolor=hover_border,
            font=dict(color=hover_text, family="Inter, system-ui, sans-serif"),
        ),
    }
    if height:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=axis,
        tickcolor=axis,
        tickfont=dict(color=t["muted"]),
        title_font=dict(color=t["muted"]),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid,
        gridwidth=1,
        zeroline=False,
        linecolor=axis,
        tickcolor=axis,
        tickfont=dict(color=t["muted"]),
        title_font=dict(color=t["muted"]),
    )
