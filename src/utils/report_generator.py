import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from src.db.database_manager import DatabaseManager
from src.utils.logger import logger
from config import config

# Try importing reportlab for PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ReportGenerator:
    """Compiles session safety statistics from SQLite and exports styled PDF/HTML reports."""
    
    def __init__(self, db_manager: DatabaseManager, reports_dir: Path = config.db_path.parent / "reports"):
        self.db = db_manager
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _fetch_session_data(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Queries database for session metadata and telemetry logs."""
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                
                # Fetch session details
                cursor.execute(
                    """
                    SELECT s.id, u.username, s.start_time, s.end_time, 
                           s.total_drowsiness_alerts, s.total_distraction_alerts, s.status
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.id = ?;
                    """,
                    (session_id,)
                )
                session_row = cursor.fetchone()
                if not session_row:
                    return None
                
                # Fetch logged violations
                cursor.execute(
                    """
                    SELECT timestamp, event_type, ear_value, mar_value, head_pitch, head_yaw, action_taken
                    FROM events 
                    WHERE session_id = ? AND event_type != 'NORMAL'
                    ORDER BY id ASC;
                    """,
                    (session_id,)
                )
                events = [dict(row) for row in cursor.fetchall()]
                
                data = dict(session_row)
                data["events"] = events
                return data
        except Exception as e:
            logger.error(f"ReportGenerator: Failed to fetch session data: {e}")
            return None

    def generate_report(self, session_id: int) -> Optional[Path]:
        """
        Main entrypoint. Compiles session log and exports a report file.
        Prefer PDF output if ReportLab is installed, otherwise fall back to HTML.
        """
        data = self._fetch_session_data(session_id)
        if not data:
            logger.error(f"ReportGenerator: No data found for session ID: {session_id}")
            return None

        if REPORTLAB_AVAILABLE:
            return self._generate_pdf(session_id, data)
        else:
            logger.warning("ReportGenerator: 'reportlab' is missing. Falling back to HTML report format.")
            return self._generate_html(session_id, data)

    def _generate_pdf(self, session_id: int, data: Dict[str, Any]) -> Optional[Path]:
        """Generates a professional PDF session report."""
        pdf_path = self.reports_dir / f"session_report_{session_id}.pdf"
        
        try:
            # Setup document layout
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
            )
            
            styles = getSampleStyleSheet()
            
            # Custom ParagraphStyles
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#002B49'), # Deep Navy
                spaceAfter=15
            )
            
            h2_style = ParagraphStyle(
                'ReportH2',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#FF6D00'), # Orange highlight
                spaceBefore=12,
                spaceAfter=8
            )
            
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['BodyText'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#333333')
            )

            story = []
            
            # Header
            story.append(Paragraph("🛡️ Driver Safety Assessment Session Report", title_style))
            story.append(Spacer(1, 10))
            
            # Metadata Table
            meta_data = [
                [Paragraph("<b>Session ID:</b>", body_style), Paragraph(str(data["id"]), body_style),
                 Paragraph("<b>Driver Profile:</b>", body_style), Paragraph(data["username"], body_style)],
                [Paragraph("<b>Start Time:</b>", body_style), Paragraph(data["start_time"], body_style),
                 Paragraph("<b>End Time:</b>", body_style), Paragraph(str(data["end_time"] or "Active"), body_style)],
                [Paragraph("<b>Drowsiness Violations:</b>", body_style), Paragraph(str(data["total_drowsiness_alerts"]), body_style),
                 Paragraph("<b>Distraction Violations:</b>", body_style), Paragraph(str(data["total_distraction_alerts"]), body_style)],
                [Paragraph("<b>Completion Status:</b>", body_style), Paragraph(data["status"], body_style),
                 Paragraph("<b>Export Date:</b>", body_style), Paragraph(time.strftime("%Y-%m-%d %H:%M:%S"), body_style)]
            ]
            
            t_meta = Table(meta_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
            t_meta.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F7FA')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            
            story.append(t_meta)
            story.append(Spacer(1, 15))
            
            # Violations Log Section
            story.append(Paragraph("📋 Telemetry Alert Log Details", h2_style))
            
            events = data["events"]
            if not events:
                story.append(Paragraph("No safety alerts or threshold violations were recorded during this driving session.", body_style))
            else:
                # Table headers
                log_data = [[
                    Paragraph("<b>Timestamp</b>", body_style),
                    Paragraph("<b>Event Type</b>", body_style),
                    Paragraph("<b>EAR</b>", body_style),
                    Paragraph("<b>MAR</b>", body_style),
                    Paragraph("<b>Pitch/Yaw</b>", body_style),
                    Paragraph("<b>Action</b>", body_style)
                ]]
                
                for ev in events:
                    log_data.append([
                        Paragraph(ev["timestamp"].split()[-1], body_style), # only show clock time
                        Paragraph(ev["event_type"], body_style),
                        Paragraph(f"{ev['ear_value']:.3f}" if ev['ear_value'] else "N/A", body_style),
                        Paragraph(f"{ev['mar_value']:.3f}" if ev['mar_value'] else "N/A", body_style),
                        Paragraph(f"{ev['head_pitch']:.1f}/{ev['head_yaw']:.1f}" if ev['head_pitch'] else "N/A", body_style),
                        Paragraph(ev["action_taken"], body_style)
                    ])
                    
                t_log = Table(log_data, colWidths=[1.1*inch, 1.5*inch, 1.0*inch, 1.0*inch, 1.3*inch, 1.3*inch])
                t_log.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(t_log)
                
            story.append(Spacer(1, 25))
            story.append(Paragraph("<font size=8 color='#A0AEC0'>Report compiled automatically by the Intelligent Driver Safety & Drowsiness Prevention System.</font>", body_style))
            
            # Compile PDF
            doc.build(story)
            logger.info(f"ReportGenerator: Generated PDF session report: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"ReportGenerator: PDF generation failed: {e}")
            return None

    def _generate_html(self, session_id: int, data: Dict[str, Any]) -> Optional[Path]:
        """Generates a styled fallback HTML session report."""
        html_path = self.reports_dir / f"session_report_{session_id}.html"
        
        try:
            rows_html = ""
            for ev in data["events"]:
                ear_str = f"{ev['ear_value']:.3f}" if ev.get('ear_value') is not None else 'N/A'
                mar_str = f"{ev['mar_value']:.3f}" if ev.get('mar_value') is not None else 'N/A'
                if ev.get('head_pitch') is not None and ev.get('head_yaw') is not None:
                    pose_str = f"{ev['head_pitch']:.1f}/{ev['head_yaw']:.1f}"
                else:
                    pose_str = "N/A"
                
                rows_html += f"""
                <tr>
                    <td>{ev['timestamp']}</td>
                    <td class="badge">{ev['event_type']}</td>
                    <td>{ear_str}</td>
                    <td>{mar_str}</td>
                    <td>{pose_str}</td>
                    <td>{ev['action_taken']}</td>
                </tr>
                """
                
            if not data["events"]:
                rows_html = "<tr><td colspan='6' style='text-align:center;'>No safety alerts recorded.</td></tr>"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Safety Assessment Report - Session {session_id}</title>
                <style>
                    body {{ font-family: 'Outfit', 'Segoe UI', Arial, sans-serif; background: #F8FAFC; color: #1E293B; margin: 40px; }}
                    .container {{ max-width: 800px; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin: 0 auto; }}
                    h1 {{ color: #002B49; margin-bottom: 5px; }}
                    h2 {{ color: #FF6D00; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-top: 30px; }}
                    .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; background: #F1F5F9; padding: 20px; border-radius: 8px; margin-top: 20px; }}
                    .meta-item {{ font-size: 14px; }}
                    .meta-label {{ font-weight: 700; color: #475569; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
                    th {{ background: #E2E8F0; text-align: left; padding: 10px; font-weight: 600; }}
                    td {{ padding: 10px; border-bottom: 1px solid #E2E8F0; }}
                    tr:nth-child(even) {{ background: #F8FAFC; }}
                    .badge {{ font-weight: 600; color: #D97706; }}
                    .footer {{ font-size: 11px; color: #94A3B8; margin-top: 40px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🛡️ Driver Safety Assessment Report</h1>
                    <div style="color: #64748B; font-size: 14px;">Intelligent Driver Safety & Drowsiness Prevention System</div>
                    
                    <div class="meta-grid">
                        <div class="meta-item"><span class="meta-label">Session ID:</span> {data['id']}</div>
                        <div class="meta-item"><span class="meta-label">Driver Profile:</span> {data['username']}</div>
                        <div class="meta-item"><span class="meta-label">Start Time:</span> {data['start_time']}</div>
                        <div class="meta-item"><span class="meta-label">End Time:</span> {data['end_time'] or 'Active'}</div>
                        <div class="meta-item"><span class="meta-label">Drowsiness Alerts:</span> {data['total_drowsiness_alerts']}</div>
                        <div class="meta-item"><span class="meta-label">Distraction Alerts:</span> {data['total_distraction_alerts']}</div>
                        <div class="meta-item"><span class="meta-label">Status:</span> {data['status']}</div>
                        <div class="meta-item"><span class="meta-label">Export Time:</span> {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
                    </div>
                    
                    <h2>📋 Telemetry Violation Logs</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Event Type</th>
                                <th>EAR</th>
                                <th>MAR</th>
                                <th>Pitch/Yaw</th>
                                <th>Action Taken</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                    
                    <div class="footer">
                        Report generated automatically. Print to PDF via browser dialog (Ctrl+P).
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open(html_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
            logger.info(f"ReportGenerator: Generated fallback HTML session report: {html_path}")
            return html_path
        except Exception as e:
            logger.error(f"ReportGenerator: HTML generation failed: {e}")
            return None
