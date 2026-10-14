"""
Export Quotations Report Modal Dialog:
Provides comprehensive filtering by Timeframe / Date Range, Sales Representative,
and Status ('Only Won', 'Only Open', 'Only In-Review', 'Only Lost', 'All Statuses'),
with instant one-click publication to Executive PDF or CSV Spreadsheet.
"""
import os
import tkinter.messagebox as msgbox
from datetime import date, datetime, timedelta
import customtkinter as ctk

from app.ui.theme import Theme
from app.database.models import SalesPerson, Quotation
from app.services.report_service import ReportService
from app.services.report_pdf_service import ReportPDFGenerator


def open_quotations_export_dialog(parent, default_status="All", default_salesperson_id=None):
    """Opens modern modal dialog to filter quotations by date range, salesperson and status, then export as PDF or CSV."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Export Quotations Audit Report")
    dialog.geometry("540x620")
    dialog.resizable(False, False)
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()

    # Center window over parent
    try:
        dialog.update_idletasks()
        pw = parent.winfo_toplevel().winfo_width()
        ph = parent.winfo_toplevel().winfo_height()
        px = parent.winfo_toplevel().winfo_x()
        py = parent.winfo_toplevel().winfo_y()
        dx = px + (pw - 540) // 2
        dy = py + (ph - 620) // 2
        dialog.geometry(f"540x620+{max(0, dx)}+{max(0, dy)}")
    except Exception:
        pass

    # Header
    head_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    head_frame.pack(fill="x", padx=24, pady=(20, 14))

    ctk.CTkLabel(
        head_frame,
        text="📊 Export Quotations Audit Report",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=18, weight="bold"),
        text_color=(Theme.BLACK, Theme.PAPER),
    ).pack(anchor="w")

    ctk.CTkLabel(
        head_frame,
        text="Export itemized quotation records by timeframe, sales executive & status.",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
        text_color=("#615D56", "#A8A297"),
    ).pack(anchor="w", pady=(2, 0))

    body = ctk.CTkFrame(dialog, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    # 1. Preset Dropdown
    ctk.CTkLabel(
        body,
        text="📅 Timeframe Preset:",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
        text_color=(Theme.BLACK, Theme.PAPER)
    ).pack(anchor="w", pady=(4, 3))

    presets = [
        "This Month",
        "Today",
        "This Week",
        "Last Month",
        "Last 30 Days",
        "This Year",
        "All Time",
        "Custom Range",
    ]

    # Date Entry Fields
    dates_frame = ctk.CTkFrame(body, fg_color="transparent")
    dates_frame.pack(fill="x", pady=(8, 12))
    dates_frame.columnconfigure((0, 1), weight=1)

    # From Date
    f_box = ctk.CTkFrame(dates_frame, fg_color="transparent")
    f_box.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
    ctk.CTkLabel(
        f_box,
        text="From Date (YYYY-MM-DD):",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
        text_color=(Theme.BLACK, Theme.PAPER)
    ).pack(anchor="w", pady=(0, 3))

    from_ent = ctk.CTkEntry(
        f_box,
        height=34,
        corner_radius=Theme.RADIUS_INPUT,
        fg_color=Theme.INSET_BG,
        border_color=Theme.INSET_BORDER,
        border_width=Theme.BORDER_WIDTH_INPUT,
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
        placeholder_text="YYYY-MM-DD"
    )
    from_ent.pack(fill="x")

    # To Date
    t_box = ctk.CTkFrame(dates_frame, fg_color="transparent")
    t_box.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
    ctk.CTkLabel(
        t_box,
        text="To Date (YYYY-MM-DD):",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
        text_color=(Theme.BLACK, Theme.PAPER)
    ).pack(anchor="w", pady=(0, 3))

    to_ent = ctk.CTkEntry(
        t_box,
        height=34,
        corner_radius=Theme.RADIUS_INPUT,
        fg_color=Theme.INSET_BG,
        border_color=Theme.INSET_BORDER,
        border_width=Theme.BORDER_WIDTH_INPUT,
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
        placeholder_text="YYYY-MM-DD"
    )
    to_ent.pack(fill="x")

    def on_preset_selected(preset_val):
        today = date.today()
        from_ent.delete(0, "end")
        to_ent.delete(0, "end")

        if preset_val == "Today":
            from_ent.insert(0, today.strftime("%Y-%m-%d"))
            to_ent.insert(0, today.strftime("%Y-%m-%d"))
        elif preset_val == "This Week":
            monday = today - timedelta(days=today.weekday())
            from_ent.insert(0, monday.strftime("%Y-%m-%d"))
            to_ent.insert(0, today.strftime("%Y-%m-%d"))
        elif preset_val == "This Month":
            first_day = today.replace(day=1)
            from_ent.insert(0, first_day.strftime("%Y-%m-%d"))
            to_ent.insert(0, today.strftime("%Y-%m-%d"))
        elif preset_val == "Last Month":
            first_this = today.replace(day=1)
            last_prev = first_this - timedelta(days=1)
            first_prev = last_prev.replace(day=1)
            from_ent.insert(0, first_prev.strftime("%Y-%m-%d"))
            to_ent.insert(0, last_prev.strftime("%Y-%m-%d"))
        elif preset_val == "Last 30 Days":
            start_30 = today - timedelta(days=30)
            from_ent.insert(0, start_30.strftime("%Y-%m-%d"))
            to_ent.insert(0, today.strftime("%Y-%m-%d"))
        elif preset_val == "This Year":
            start_yr = date(today.year, 1, 1)
            from_ent.insert(0, start_yr.strftime("%Y-%m-%d"))
            to_ent.insert(0, today.strftime("%Y-%m-%d"))
        elif preset_val == "All Time":
            pass
        elif preset_val == "Custom Range":
            first_day = today.replace(day=1)
            from_ent.insert(0, first_day.strftime("%Y-%m-%d"))
            to_ent.insert(0, today.strftime("%Y-%m-%d"))

    preset_menu = ctk.CTkOptionMenu(
        body,
        values=presets,
        command=on_preset_selected,
        height=34,
        corner_radius=Theme.RADIUS_PILL,
        fg_color=Theme.BTN_SECONDARY_BG,
        text_color=(Theme.BLACK, Theme.PAPER),
        button_color=Theme.PRIMARY,
        button_hover_color=Theme.PRIMARY_HOVER,
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
    )
    preset_menu.pack(fill="x", pady=(0, 4))
    preset_menu.set("This Month")
    on_preset_selected("This Month")

    # 2. Salesperson Dropdown
    ctk.CTkLabel(
        body,
        text="👤 Filter by Sales Representative:",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
        text_color=(Theme.BLACK, Theme.PAPER)
    ).pack(anchor="w", pady=(8, 3))

    all_salespersons = list(SalesPerson.select().where(SalesPerson.is_active == True).order_by(SalesPerson.name))
    sp_names = ["All Sales Associates"] + [sp.name for sp in all_salespersons]
    sp_menu = ctk.CTkOptionMenu(
        body,
        values=sp_names,
        height=34,
        corner_radius=Theme.RADIUS_PILL,
        fg_color=Theme.BTN_SECONDARY_BG,
        text_color=(Theme.BLACK, Theme.PAPER),
        button_color=Theme.PRIMARY,
        button_hover_color=Theme.PRIMARY_HOVER,
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
    )
    sp_menu.pack(fill="x", pady=(0, 4))

    selected_sp_name = "All Sales Associates"
    if default_salesperson_id:
        for sp in all_salespersons:
            if sp.id == default_salesperson_id:
                selected_sp_name = sp.name
                break
    sp_menu.set(selected_sp_name)

    # 3. Status Filter Dropdown
    ctk.CTkLabel(
        body,
        text="🏷️ Filter by Quotation Status:",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
        text_color=(Theme.BLACK, Theme.PAPER)
    ).pack(anchor="w", pady=(8, 3))

    status_options = [
        "All Statuses",
        "Only Won",
        "Only Open",
        "Only In-Review",
        "Only Lost",
    ]
    status_menu = ctk.CTkOptionMenu(
        body,
        values=status_options,
        height=34,
        corner_radius=Theme.RADIUS_PILL,
        fg_color=Theme.BTN_SECONDARY_BG,
        text_color=(Theme.BLACK, Theme.PAPER),
        button_color=Theme.PRIMARY,
        button_hover_color=Theme.PRIMARY_HOVER,
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
    )
    status_menu.pack(fill="x", pady=(0, 4))

    cur_st = str(default_status or "All").strip()
    if cur_st.lower() in ("won", "only won"):
        status_menu.set("Only Won")
    elif cur_st.lower() in ("open", "only open"):
        status_menu.set("Only Open")
    elif cur_st.lower() in ("in-review", "in review", "only in-review", "only in review"):
        status_menu.set("Only In-Review")
    elif cur_st.lower() in ("lost", "only lost"):
        status_menu.set("Only Lost")
    else:
        status_menu.set("All Statuses")

    # 4. Info Card / Format Guide
    info_card = ctk.CTkFrame(
        body,
        fg_color=Theme.INSET_BG,
        border_width=1,
        border_color=Theme.INSET_BORDER,
        corner_radius=Theme.RADIUS_MD
    )
    info_card.pack(fill="x", pady=(14, 10), ipady=6)

    ctk.CTkLabel(
        info_card,
        text="📄 Report Scope & Financial Summary",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
        text_color=Theme.PRIMARY,
    ).pack(anchor="w", padx=12, pady=(4, 2))

    ctk.CTkLabel(
        info_card,
        text="• Generates itemized registry with Sl, Quote #, Date, Customer & Phone, Sales Rep, Status, Net Total, Cleared Payments & Balance.\n• Executive KPI summary cards for Quoted Value, Cleared Collections, and Outstanding Balances.\n• Accounts for primary sales reps and assisted deal splits automatically.",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
        text_color=("#615D56", "#A8A297"),
        justify="left",
        wraplength=460,
    ).pack(anchor="w", padx=12, pady=(0, 4))

    # Bottom Buttons Bar
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=24, pady=(0, 20))

    def do_export(fmt="pdf"):
        s_date = from_ent.get().strip() or None
        e_date = to_ent.get().strip() or None

        chosen_sp_name = sp_menu.get()
        chosen_sp_id = None
        if chosen_sp_name != "All Sales Associates":
            for sp in all_salespersons:
                if sp.name == chosen_sp_name:
                    chosen_sp_id = sp.id
                    break

        chosen_status = status_menu.get()

        try:
            if fmt == "pdf":
                out_path = ReportPDFGenerator.generate_quotations_report_pdf(
                    start_date=s_date,
                    end_date=e_date,
                    sales_person_id=chosen_sp_id,
                    status=chosen_status
                )
                dialog.destroy()
                msgbox.showinfo(
                    "PDF Export Complete",
                    f"Quotations Audit Report PDF generated successfully!\n\nFilter: {chosen_status}\nFile saved at:\n{out_path}"
                )
                try:
                    os.startfile(out_path)
                except Exception:
                    pass
            else:
                out_path = ReportService.export_quotations_csv(
                    start_date=s_date,
                    end_date=e_date,
                    sales_person_id=chosen_sp_id,
                    status=chosen_status
                )
                dialog.destroy()
                msgbox.showinfo(
                    "CSV Export Complete",
                    f"Quotations Spreadsheet CSV exported successfully!\n\nFilter: {chosen_status}\nFile saved at:\n{out_path}"
                )
                try:
                    os.startfile(out_path)
                except Exception:
                    pass
        except Exception as err:
            msgbox.showerror("Export Failed", f"Could not generate {fmt.upper()} report:\n{str(err)}", parent=dialog)

    # Export PDF Button
    pdf_btn = ctk.CTkButton(
        btn_frame,
        text="Export PDF 📄",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
        fg_color=Theme.PRIMARY,
        hover_color=Theme.PRIMARY_HOVER,
        corner_radius=Theme.RADIUS_PILL,
        border_width=Theme.BORDER_WIDTH_BUTTON,
        border_color=Theme.BTN_PRIMARY_BORDER,
        height=38,
        command=lambda: do_export("pdf")
    )
    pdf_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

    # Export CSV Button
    csv_btn = ctk.CTkButton(
        btn_frame,
        text="Export CSV 📥",
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
        fg_color=Theme.BTN_SECONDARY_BG,
        text_color=(Theme.BLACK, Theme.PAPER),
        hover_color=Theme.BTN_SECONDARY_HOVER,
        corner_radius=Theme.RADIUS_PILL,
        border_width=Theme.BORDER_WIDTH_BUTTON,
        border_color=Theme.BTN_SECONDARY_BORDER,
        height=38,
        command=lambda: do_export("csv")
    )
    csv_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

    # Cancel Button
    cancel_btn = ctk.CTkButton(
        btn_frame,
        text="Cancel",
        width=75,
        height=38,
        font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
        fg_color="transparent",
        hover_color=Theme.BTN_SECONDARY_HOVER,
        text_color=(Theme.BLACK, Theme.PAPER),
        command=dialog.destroy
    )
    cancel_btn.pack(side="left")

    return dialog
