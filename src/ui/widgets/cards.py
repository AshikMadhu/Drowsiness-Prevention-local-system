import streamlit as st

def render_styled_card(title: str, value: str, subtext: str = "", color_theme: str = "blue") -> str:
    """
    Renders a custom HTML/CSS glassmorphism metric card.
    Themes: blue, yellow, orange, red, green, gray
    """
    theme_colors = {
        "blue": ("#0A84FF", "rgba(10, 132, 255, 0.08)", "rgba(10, 132, 255, 0.15)"),
        "green": ("#30D158", "rgba(48, 209, 88, 0.08)", "rgba(48, 209, 88, 0.15)"),
        "yellow": ("#FFD60A", "rgba(255, 214, 10, 0.08)", "rgba(255, 214, 10, 0.15)"),
        "orange": ("#FF9F0A", "rgba(255, 159, 10, 0.08)", "rgba(255, 159, 10, 0.15)"),
        "red": ("#FF453A", "rgba(255, 69, 58, 0.08)", "rgba(255, 69, 58, 0.15)"),
        "gray": ("#8E8E93", "rgba(142, 142, 147, 0.08)", "rgba(142, 142, 147, 0.15)")
    }
    
    primary, bg, border = theme_colors.get(color_theme, theme_colors["blue"])
    
    html = f"""
    <div style="
        background: {bg};
        border: 1.5px solid {border};
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        font-family: 'Outfit', 'Inter', sans-serif;
    ">
        <div style="color: #AEAEB2; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.8px;">
            {title}
        </div>
        <div style="color: {primary}; font-size: 32px; font-weight: 700; margin: 8px 0px 4px 0px; letter-spacing: -0.5px;">
            {value}
        </div>
        {f'<div style="color: #8E8E93; font-size: 11px; font-weight: 400;">{subtext}</div>' if subtext else ''}
    </div>
    """
    return html

def render_risk_card(risk_level: str) -> str:
    """Renders a customized card specifically styled for the driver's risk level."""
    levels = {
        "Safe": ("SAFE", "green", "Normal operations. Driver attentiveness verified."),
        "Warning": ("WARNING", "yellow", "Caution. Facial distraction indicators detected."),
        "Danger": ("DANGER", "orange", "Immediate Hazard. Fatigue levels are elevated!"),
        "Critical": ("CRITICAL SOS", "red", "Severe Danger! Driver is unresponsive! Escalating alerts.")
    }
    
    display_title, theme, desc = levels.get(risk_level, ("UNKNOWN", "gray", "Awaiting telemetry..."))
    
    # Pulse animation for critical alerts
    pulse_style = """
    <style>
    @keyframes pulse-red {
        0% { opacity: 1; box-shadow: 0 0 0 0 rgba(255, 69, 58, 0.4); }
        70% { opacity: 1; box-shadow: 0 0 0 10px rgba(255, 69, 58, 0); }
        100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255, 69, 58, 0); }
    }
    .pulse-card-critical {
        animation: pulse-red 2s infinite;
    }
    </style>
    """
    
    card_html = render_styled_card("ACTIVE RISK LEVEL", display_title, desc, theme)
    
    if risk_level == "Critical":
        # Inject pulsing shadow wrapper
        card_html = card_html.replace('border-radius: 12px;', 'border-radius: 12px; animation: pulse-red 1.5s infinite;')
        return pulse_style + card_html
        
    return card_html

def render_emergency_status_card(is_dispatched: bool) -> str:
    """Renders the emergency status card, detailing dispatch statuses of Level 4 emails."""
    if is_dispatched:
        html = f"""
        <div style="
            background: rgba(255, 69, 58, 0.12);
            border: 2px solid #FF453A;
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0px;
            text-align: center;
            font-family: 'Outfit', 'Inter', sans-serif;
            animation: pulse-red 1s infinite;
        ">
            <span style="color: #FF453A; font-size: 18px; font-weight: 700; display: inline-flex; align-items: center; gap: 8px;">
                🚨 EMERGENCY ALERT BROADCASTED
            </span>
            <div style="color: #FFFFFF; font-size: 12px; margin-top: 4px;">
                Email notification dispatched to emergency contacts.
            </div>
        </div>
        """
    else:
        html = """
        <div style="
            background: rgba(48, 209, 88, 0.08);
            border: 1.5px solid rgba(48, 209, 88, 0.2);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0px;
            text-align: center;
            font-family: 'Outfit', 'Inter', sans-serif;
        ">
            <span style="color: #30D158; font-size: 16px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px;">
                🛡️ Safety Monitors Nominal
            </span>
            <div style="color: #8E8E93; font-size: 11px; margin-top: 4px;">
                No emergency triggers activated.
            </div>
        </div>
        """
    return html
