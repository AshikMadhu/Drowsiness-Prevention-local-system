import plotly.graph_objects as go
from typing import List

def create_realtime_metrics_plot(
    ear_history: List[float],
    mar_history: List[float],
    ear_threshold: float,
    mar_threshold: float
) -> go.Figure:
    """
    Generates a dark-themed, responsive Plotly chart displaying rolling EAR and MAR trends.
    """
    fig = go.Figure()
    
    # x-axis coordinates (sample frames index)
    x_coords = list(range(len(ear_history)))
    
    # 1. Plot EAR Line (Cyan)
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=ear_history,
        name="Eye Aspect Ratio (EAR)",
        mode="lines",
        line=dict(color="#00F0FF", width=2.5),
        fill='tozeroy',
        fillcolor='rgba(0, 240, 255, 0.05)'
    ))
    
    # 2. Plot MAR Line (Orange)
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=mar_history,
        name="Mouth Aspect Ratio (MAR)",
        mode="lines",
        line=dict(color="#FF9E00", width=2.5),
        fill='tozeroy',
        fillcolor='rgba(255, 158, 0, 0.05)'
    ))

    # 3. Add EAR Threshold horizontal indicator (Red Dotted)
    fig.add_hline(
        y=ear_threshold,
        line_dash="dash",
        line_color="#FF3B30",
        line_width=1.5,
        annotation_text="EAR Threshold",
        annotation_position="top left",
        annotation_font=dict(color="#FF3B30", size=10)
    )

    # 4. Add MAR Threshold horizontal indicator (Yellow Dotted)
    fig.add_hline(
        y=mar_threshold,
        line_dash="dash",
        line_color="#FFCC00",
        line_width=1.5,
        annotation_text="MAR Yawn Threshold",
        annotation_position="top left",
        annotation_font=dict(color="#FFCC00", size=10)
    )

    # Apply layout stylings (Premium Dark UI aesthetics)
    fig.update_layout(
        title=dict(
            text="Real-Time Driver Biometrics Trend (EAR / MAR)",
            font=dict(color="#FFFFFF", size=16, family="Outfit, sans-serif")
        ),
        paper_bgcolor="rgba(17, 18, 23, 0.9)", # Glassmorphism dark card feel
        plot_bgcolor="rgba(17, 18, 23, 0.9)",
        xaxis=dict(
            title=dict(text="Recent Frames Timeline", font=dict(color="#AEAEB2", size=12)),
            gridcolor="#2A2C35",
            tickfont=dict(color="#8E8E93"),
            showgrid=True
        ),
        yaxis=dict(
            title=dict(text="Aspect Ratio Value", font=dict(color="#AEAEB2", size=12)),
            gridcolor="#2A2C35",
            tickfont=dict(color="#8E8E93"),
            range=[0.0, 1.0],
            showgrid=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(color="#FFFFFF", size=11)
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        height=320,
        hovermode="x unified"
    )
    
    return fig
