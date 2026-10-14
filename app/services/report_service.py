"""
Report Service: Data aggregation for reporting dashboards,
salesperson performance, receivables breakdown, and timeframe analytics.
"""
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from peewee import fn

from app.config import OUTPUT_PDF_DIR
from app.database.models import Quotation, Payment, SalesPerson, Customer


class ReportService:
    @staticmethod
    def get_timeframe_dates(timeframe: str):
        """Returns start and end dates based on filter: Daily, Weekly, Monthly, All."""
        today = date.today()
        if timeframe == "Daily":
            start_date = today
            end_date = today
        elif timeframe == "Weekly":
            start_date = today - timedelta(days=7)
            end_date = today
        elif timeframe == "Monthly":
            start_date = today.replace(day=1)
            end_date = today
        else:  # All Time
            start_date = date(2020, 1, 1)
            end_date = today
        return start_date, end_date

    @staticmethod
    def get_dashboard_metrics(timeframe: str = "Monthly"):
        """Calculates key metrics for the dashboard KPI cards."""
        start_date, end_date = ReportService.get_timeframe_dates(timeframe)

        # Base quotes in period
        quote_query = Quotation.select().where(
            (Quotation.quotation_date >= start_date) &
            (Quotation.quotation_date <= end_date)
        )

        total_quotes_count = quote_query.count()
        won_quotes_count = quote_query.where(Quotation.status == Quotation.STATUS_WON).count()
        open_quotes_count = quote_query.where(Quotation.status == Quotation.STATUS_OPEN).count()
        in_review_count = quote_query.where(Quotation.status == Quotation.STATUS_IN_REVIEW).count()
        lost_quotes_count = quote_query.where(Quotation.status == Quotation.STATUS_LOST).count()

        # Gross & Net value of Won quotes
        won_sales_val = (
            Quotation.select(fn.SUM(Quotation.net_total))
            .where(
                (Quotation.quotation_date >= start_date) &
                (Quotation.quotation_date <= end_date) &
                (Quotation.status == Quotation.STATUS_WON)
            ).scalar() or 0.0
        )

        # Pipeline value (Open + In-Review)
        pipeline_val = (
            Quotation.select(fn.SUM(Quotation.net_total))
            .where(
                (Quotation.quotation_date >= start_date) &
                (Quotation.quotation_date <= end_date) &
                (Quotation.status.in_([Quotation.STATUS_OPEN, Quotation.STATUS_IN_REVIEW]))
            ).scalar() or 0.0
        )

        # Payments in this period
        cleared_payments = (
            Payment.select(fn.SUM(Payment.amount))
            .where(
                (Payment.payment_date >= start_date) &
                (Payment.payment_date <= end_date) &
                (Payment.status == Payment.STATUS_CLEARED)
            ).scalar() or 0.0
        )

        pending_payments = (
            Payment.select(fn.SUM(Payment.amount))
            .where(
                (Payment.payment_date >= start_date) &
                (Payment.payment_date <= end_date) &
                (Payment.status == Payment.STATUS_PENDING)
            ).scalar() or 0.0
        )

        # Total outstanding balance across won quotations (single-query aggregate)
        total_won_net = float(
            Quotation.select(fn.SUM(Quotation.net_total))
            .where(Quotation.status == Quotation.STATUS_WON)
            .scalar() or 0.0
        )
        total_won_cleared = float(
            Payment.select(fn.SUM(Payment.amount))
            .join(Quotation)
            .where(
                (Quotation.status == Quotation.STATUS_WON) &
                (Payment.status == Payment.STATUS_CLEARED)
            )
            .scalar() or 0.0
        )
        total_outstanding = max(0.0, total_won_net - total_won_cleared)

        conversion_rate = (won_quotes_count / total_quotes_count * 100.0) if total_quotes_count > 0 else 0.0

        return {
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "total_quotes": total_quotes_count,
            "won_quotes": won_quotes_count,
            "open_quotes": open_quotes_count,
            "in_review_quotes": in_review_count,
            "lost_quotes": lost_quotes_count,
            "won_sales_value": float(won_sales_val),
            "pipeline_value": float(pipeline_val),
            "cleared_payments": float(cleared_payments),
            "pending_payments": float(pending_payments),
            "total_outstanding": float(total_outstanding),
            "conversion_rate": round(conversion_rate, 1),
        }

    @staticmethod
    def get_salesperson_performances(timeframe_or_start="Monthly", end_date_arg=None):
        """Calculates each salesperson's target, achieved sales, balance, and %."""
        if isinstance(timeframe_or_start, date):
            start_date = timeframe_or_start
            end_date = end_date_arg if isinstance(end_date_arg, date) else timeframe_or_start
        elif end_date_arg is not None and isinstance(end_date_arg, date):
            start_date, end_date = timeframe_or_start, end_date_arg
        else:
            timeframe = timeframe_or_start if isinstance(timeframe_or_start, str) else "Monthly"
            start_date, end_date = ReportService.get_timeframe_dates(timeframe)
        sales_team = list(SalesPerson.select().where(SalesPerson.is_active == True))

        results = []
        team_total_target = 0.0
        team_total_achieved = 0.0

        for sp in sales_team:
            # Sales achieved in timeframe from Won quotes (properly attributing primary and assisted shares!)
            achieved = sp.get_sales_achieved(start_date=start_date, end_date=end_date)
            pipeline = sp.get_pipeline_value(start_date=start_date, end_date=end_date)

            effective_target = sp.get_target_for_period(start_date, end_date)

            balance = max(0.0, effective_target - achieved)
            pct = (achieved / effective_target * 100.0) if effective_target > 0 else 0.0

            team_total_target += effective_target
            team_total_achieved += achieved

            results.append({
                "id": sp.id,
                "name": sp.name,
                "role": sp.role,
                "contact": sp.contact_number,
                "target": round(effective_target, 2),
                "achieved": round(achieved, 2),
                "pipeline": round(pipeline, 2),
                "balance": round(balance, 2),
                "percentage": round(pct, 1),
            })

        team_balance = max(0.0, team_total_target - team_total_achieved)
        team_pct = (team_total_achieved / team_total_target * 100.0) if team_total_target > 0 else 0.0

        return {
            "individuals": results,
            "team_total_target": round(team_total_target, 2),
            "team_total_achieved": round(team_total_achieved, 2),
            "team_balance": round(team_balance, 2),
            "team_percentage": round(team_pct, 1),
        }

    # =========================================================================
    # 1. DAILY REPORT DATA & EXPORT
    # =========================================================================
    @staticmethod
    def get_daily_report_data(target_date: date = None):
        """Fetches comprehensive audit data for a specific day."""
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except Exception:
                target_date = date.today()

        quotes = list(
            Quotation.select().where(Quotation.quotation_date == target_date).order_by(Quotation.created_at.desc())
        )
        if quotes:
            q_ids = [q.id for q in quotes]
            cleared_sums = dict(
                Payment.select(Payment.quotation_id, fn.SUM(Payment.amount))
                .where(
                    (Payment.quotation_id.in_(q_ids)) &
                    (Payment.status == Payment.STATUS_CLEARED)
                )
                .group_by(Payment.quotation_id)
                .tuples()
            )
            for q in quotes:
                q._cached_cleared_payments = float(cleared_sums.get(q.id, 0.0) or 0.0)

        total_quotes = len(quotes)
        won_quotes = [q for q in quotes if q.status == Quotation.STATUS_WON]
        open_quotes = [q for q in quotes if q.status == Quotation.STATUS_OPEN]
        in_review_quotes = [q for q in quotes if q.status == Quotation.STATUS_IN_REVIEW]
        lost_quotes = [q for q in quotes if q.status == Quotation.STATUS_LOST]

        total_gross = sum(q.gross_total for q in quotes)
        total_net = sum(q.net_total for q in quotes)
        won_sales_val = sum(q.net_total for q in won_quotes)
        pipeline_val = sum(q.net_total for q in (open_quotes + in_review_quotes))

        payments = list(
            Payment.select().where(Payment.payment_date == target_date).order_by(Payment.created_at.desc())
        )
        cleared_payments = [p for p in payments if p.status == Payment.STATUS_CLEARED]
        pending_payments = [p for p in payments if p.status == Payment.STATUS_PENDING]
        cleared_total = sum(p.amount for p in cleared_payments)
        pending_total = sum(p.amount for p in pending_payments)

        sales_team = list(SalesPerson.select().where(SalesPerson.is_active == True))
        team_perf = []
        for sp in sales_team:
            daily_target = round(sp.get_target_for_month(target_date.year, target_date.month) / 26.0, 2)
            sp_quotes = [q for q in quotes if q.sales_person_id == sp.id or getattr(q, 'assisted_by_id', None) == sp.id]
            sp_won = [q for q in sp_quotes if q.status == Quotation.STATUS_WON]
            sp_achieved = sum(q.get_credit_for_salesperson(sp.id) for q in sp_won)
            pct = (sp_achieved / daily_target * 100.0) if daily_target > 0 else 0.0
            team_perf.append({
                "sales_person": sp,
                "name": sp.name,
                "role": sp.role,
                "daily_target": daily_target,
                "achieved": round(sp_achieved, 2),
                "quotes_count": len(sp_quotes),
                "won_count": len(sp_won),
                "percentage": round(pct, 1),
            })

        return {
            "target_date": target_date,
            "total_quotes": total_quotes,
            "won_quotes_count": len(won_quotes),
            "open_quotes_count": len(open_quotes),
            "in_review_quotes_count": len(in_review_quotes),
            "lost_quotes_count": len(lost_quotes),
            "total_gross": round(total_gross, 2),
            "total_net": round(total_net, 2),
            "won_sales_val": round(won_sales_val, 2),
            "pipeline_val": round(pipeline_val, 2),
            "cleared_payments_count": len(cleared_payments),
            "cleared_total": round(cleared_total, 2),
            "pending_payments_count": len(pending_payments),
            "pending_total": round(pending_total, 2),
            "quotes": quotes,
            "payments": payments,
            "team_perf": team_perf,
        }

    @staticmethod
    def export_daily_report_csv(target_date: date = None, output_filepath: str = None) -> str:
        """Exports daily sales & collections report to CSV format."""
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except Exception:
                target_date = date.today()

        data = ReportService.get_daily_report_data(target_date)
        if not output_filepath:
            output_filepath = str(OUTPUT_PDF_DIR / f"Daily_Sales_Report_{target_date.strftime('%Y%m%d')}.csv")

        with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["=== DAILY SALES & COLLECTION AUDIT REPORT ==="])
            writer.writerow(["Report Date", target_date.strftime("%d %B %Y")])
            writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            writer.writerow(["--- EXECUTIVE SUMMARY ---"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Quotations Created", data["total_quotes"]])
            writer.writerow(["Won Quotations Count", data["won_quotes_count"]])
            writer.writerow(["Gross Total Quoted (INR)", f"{data['total_gross']:.2f}"])
            writer.writerow(["Net Total Quoted (INR)", f"{data['total_net']:.2f}"])
            writer.writerow(["Won Sales Revenue (INR)", f"{data['won_sales_val']:.2f}"])
            writer.writerow(["Pipeline Value (INR)", f"{data['pipeline_val']:.2f}"])
            writer.writerow(["Realized Bank Collections (INR)", f"{data['cleared_total']:.2f}"])
            writer.writerow(["Pending Token Collections (INR)", f"{data['pending_total']:.2f}"])
            writer.writerow([])
            writer.writerow(["--- QUOTATIONS CREATED TODAY ---"])
            writer.writerow(["Quote No", "Customer", "Phone", "Sales Executive", "Status", "Gross Total", "Net Total", "Cleared Paid", "Outstanding"])
            for q in data["quotes"]:
                writer.writerow([
                    q.quotation_number,
                    q.customer_name,
                    q.customer_phone,
                    q.sales_person_name,
                    q.status,
                    f"{q.gross_total:.2f}",
                    f"{q.net_total:.2f}",
                    f"{q.get_cleared_payments():.2f}",
                    f"{q.get_outstanding_balance():.2f}",
                ])
            writer.writerow([])
            writer.writerow(["--- COLLECTIONS REALIZED TODAY ---"])
            writer.writerow(["Receipt / Ref No", "Quote No", "Customer", "Payment Mode", "Amount", "Status"])
            for p in data["payments"]:
                writer.writerow([
                    p.reference_number or "N/A",
                    p.quotation.quotation_number if p.quotation else "N/A",
                    p.quotation.customer_name if p.quotation else "N/A",
                    p.payment_mode,
                    f"{p.amount:.2f}",
                    p.status,
                ])
            writer.writerow([])
            writer.writerow(["--- SALES REPRESENTATIVE DAILY ACTIVITY ---"])
            writer.writerow(["Sales Executive", "Role", "Quotes Made", "Won Sales Achieved", "Daily Target Pro-Rata", "% Achieved"])
            for rep in data["team_perf"]:
                writer.writerow([
                    rep["name"],
                    rep["role"],
                    rep["quotes_count"],
                    f"{rep['achieved']:.2f}",
                    f"{rep['daily_target']:.2f}",
                    f"{rep['percentage']:.1f}%",
                ])

        return output_filepath

    # =========================================================================
    # 2. MONTHLY REPORT DATA & EXPORT
    # =========================================================================
    @staticmethod
    def get_monthly_report_data(year: int = None, month: int = None):
        """Fetches comprehensive audit data for a specific calendar month."""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        start_date = date(year, month, 1)
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        end_date = next_month - timedelta(days=1)

        quotes = list(
            Quotation.select().where(
                (Quotation.quotation_date >= start_date) &
                (Quotation.quotation_date <= end_date)
            ).order_by(Quotation.quotation_date.desc(), Quotation.id.desc())
        )
        if quotes:
            q_ids = [q.id for q in quotes]
            cleared_sums = dict(
                Payment.select(Payment.quotation_id, fn.SUM(Payment.amount))
                .where(
                    (Payment.quotation_id.in_(q_ids)) &
                    (Payment.status == Payment.STATUS_CLEARED)
                )
                .group_by(Payment.quotation_id)
                .tuples()
            )
            for q in quotes:
                q._cached_cleared_payments = float(cleared_sums.get(q.id, 0.0) or 0.0)

        total_quotes = len(quotes)
        won_quotes = [q for q in quotes if q.status == Quotation.STATUS_WON]
        open_quotes = [q for q in quotes if q.status == Quotation.STATUS_OPEN]
        in_review_quotes = [q for q in quotes if q.status == Quotation.STATUS_IN_REVIEW]
        lost_quotes = [q for q in quotes if q.status == Quotation.STATUS_LOST]

        won_sales_val = sum(q.net_total for q in won_quotes)
        pipeline_val = sum(q.net_total for q in (open_quotes + in_review_quotes))
        conversion_rate = (len(won_quotes) / total_quotes * 100.0) if total_quotes > 0 else 0.0

        payments = list(
            Payment.select().where(
                (Payment.payment_date >= start_date) &
                (Payment.payment_date <= end_date)
            ).order_by(Payment.payment_date.desc())
        )
        cleared_payments = [p for p in payments if p.status == Payment.STATUS_CLEARED]
        pending_payments = [p for p in payments if p.status == Payment.STATUS_PENDING]
        cleared_total = sum(p.amount for p in cleared_payments)
        pending_total = sum(p.amount for p in pending_payments)

        # Single-query aggregate for total outstanding across won orders
        total_won_net = float(
            Quotation.select(fn.SUM(Quotation.net_total))
            .where(Quotation.status == Quotation.STATUS_WON)
            .scalar() or 0.0
        )
        total_won_cleared = float(
            Payment.select(fn.SUM(Payment.amount))
            .join(Quotation)
            .where(
                (Quotation.status == Quotation.STATUS_WON) &
                (Payment.status == Payment.STATUS_CLEARED)
            )
            .scalar() or 0.0
        )
        total_outstanding = max(0.0, total_won_net - total_won_cleared)

        sales_team = list(SalesPerson.select().where(SalesPerson.is_active == True))
        team_results = []
        team_total_target = 0.0
        team_total_achieved = 0.0

        for sp in sales_team:
            target = sp.get_target_for_month(year, month)
            sp_won = [q for q in won_quotes if q.sales_person_id == sp.id or getattr(q, 'assisted_by_id', None) == sp.id]
            achieved = sum(q.get_credit_for_salesperson(sp.id) for q in sp_won)
            balance = max(0.0, target - achieved)
            pct = (achieved / target * 100.0) if target > 0 else 0.0

            team_total_target += target
            team_total_achieved += achieved

            status = "Target Exceeded" if pct >= 100 else ("On Track" if pct >= 50 else "Shortfall")
            team_results.append({
                "sales_person": sp,
                "name": sp.name,
                "role": sp.role,
                "target": round(target, 2),
                "achieved": round(achieved, 2),
                "balance": round(balance, 2),
                "percentage": round(pct, 1),
                "won_count": len(sp_won),
                "status": status,
            })

        team_balance = max(0.0, team_total_target - team_total_achieved)
        team_pct = (team_total_achieved / team_total_target * 100.0) if team_total_target > 0 else 0.0

        return {
            "year": year,
            "month": month,
            "month_name": start_date.strftime("%B %Y"),
            "start_date": start_date,
            "end_date": end_date,
            "total_quotes": total_quotes,
            "won_quotes_count": len(won_quotes),
            "open_quotes_count": len(open_quotes),
            "in_review_quotes_count": len(in_review_quotes),
            "lost_quotes_count": len(lost_quotes),
            "won_sales_val": round(won_sales_val, 2),
            "pipeline_val": round(pipeline_val, 2),
            "conversion_rate": round(conversion_rate, 1),
            "cleared_total": round(cleared_total, 2),
            "pending_total": round(pending_total, 2),
            "total_outstanding": round(total_outstanding, 2),
            "quotes": quotes,
            "payments": payments,
            "team_individuals": team_results,
            "team_total_target": round(team_total_target, 2),
            "team_total_achieved": round(team_total_achieved, 2),
            "team_balance": round(team_balance, 2),
            "team_percentage": round(team_pct, 1),
        }

    @staticmethod
    def export_monthly_report_csv(year: int = None, month: int = None, output_filepath: str = None) -> str:
        """Exports monthly performance audit report to CSV format."""
        data = ReportService.get_monthly_report_data(year, month)
        if not output_filepath:
            output_filepath = str(OUTPUT_PDF_DIR / f"Monthly_Performance_Report_{data['year']}_{data['month']:02d}.csv")

        with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["=== MONTHLY PERFORMANCE & REVENUE AUDIT REPORT ==="])
            writer.writerow(["Month", data["month_name"]])
            writer.writerow(["Date Range", f"{data['start_date']} to {data['end_date']}"])
            writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            writer.writerow(["--- EXECUTIVE KPI SUMMARY ---"])
            writer.writerow(["Total Quotations Generated", data["total_quotes"]])
            writer.writerow(["Won Deals (Closed)", data["won_quotes_count"]])
            writer.writerow(["Won Sales Revenue (INR)", f"{data['won_sales_val']:.2f}"])
            writer.writerow(["Team Monthly Target (INR)", f"{data['team_total_target']:.2f}"])
            writer.writerow(["Overall Target Achievement", f"{data['team_percentage']:.1f}%"])
            writer.writerow(["Pipeline Value (INR)", f"{data['pipeline_val']:.2f}"])
            writer.writerow(["Conversion Rate", f"{data['conversion_rate']:.1f}%"])
            writer.writerow(["Realized Bank Collections (INR)", f"{data['cleared_total']:.2f}"])
            writer.writerow(["Total Outstanding Receivables (INR)", f"{data['total_outstanding']:.2f}"])
            writer.writerow([])
            writer.writerow(["--- SALES TEAM TARGET VS ACHIEVEMENT ---"])
            writer.writerow(["Sales Executive", "Role", "Monthly Target", "Won Sales Achieved", "Balance to Goal", "% Achieved", "Won Deals Count", "Status"])
            for rep in data["team_individuals"]:
                writer.writerow([
                    rep["name"],
                    rep["role"],
                    f"{rep['target']:.2f}",
                    f"{rep['achieved']:.2f}",
                    f"{rep['balance']:.2f}",
                    f"{rep['percentage']:.1f}%",
                    rep["won_count"],
                    rep["status"],
                ])
            writer.writerow([
                "TEAM TOTAL",
                "Aggregate",
                f"{data['team_total_target']:.2f}",
                f"{data['team_total_achieved']:.2f}",
                f"{data['team_balance']:.2f}",
                f"{data['team_percentage']:.1f}%",
                data["won_quotes_count"],
                "Team Total",
            ])
            writer.writerow([])
            writer.writerow(["--- QUOTATIONS OF THE MONTH ---"])
            writer.writerow(["Quote No", "Date", "Customer", "Phone", "Sales Executive", "Status", "Gross Total", "Net Total", "Cleared Paid", "Outstanding"])
            for q in data["quotes"]:
                writer.writerow([
                    q.quotation_number,
                    q.quotation_date,
                    q.customer_name,
                    q.customer_phone,
                    q.sales_person_name,
                    q.status,
                    f"{q.gross_total:.2f}",
                    f"{q.net_total:.2f}",
                    f"{q.get_cleared_payments():.2f}",
                    f"{q.get_outstanding_balance():.2f}",
                ])

        return output_filepath

    # =========================================================================
    # 3. TARGET ARCHIVE DATA & EXPORT
    # =========================================================================
    @staticmethod
    def get_target_archive_data():
        """Fetches historical target vs achievement archives across all periods and salespeople."""
        cursor = Quotation._meta.database.execute_sql(
            "SELECT DISTINCT strftime('%Y', quotation_date), strftime('%m', quotation_date) FROM quotations WHERE quotation_date IS NOT NULL ORDER BY quotation_date DESC"
        )
        periods_raw = cursor.fetchall()

        today = date.today()
        ym_set = set()
        for r in periods_raw:
            if r[0] and r[1]:
                ym_set.add((int(r[0]), int(r[1])))
        ym_set.add((today.year, today.month))
        sorted_periods = sorted(list(ym_set), key=lambda x: (x[0], x[1]), reverse=True)

        sales_team = list(SalesPerson.select().where(SalesPerson.is_active == True))

        period_archives = []
        cumulative_map = {
            sp.id: {
                "sales_person": sp,
                "name": sp.name,
                "role": sp.role,
                "total_target": 0.0,
                "total_achieved": 0.0,
                "total_won_count": 0,
                "total_collections": 0.0,
            }
            for sp in sales_team
        }

        total_archive_target = 0.0
        total_archive_achieved = 0.0
        total_archive_collections = 0.0

        for y, m in sorted_periods:
            m_date = date(y, m, 1)
            period_label = m_date.strftime("%B %Y")

            if m == 12:
                next_m = date(y + 1, 1, 1)
            else:
                next_m = date(y, m + 1, 1)
            end_m = next_m - timedelta(days=1)

            period_reps = []
            p_total_target = 0.0
            p_total_achieved = 0.0
            p_total_won = 0
            p_total_col = 0.0

            for sp in sales_team:
                target = sp.get_target_for_month(y, m)
                achieved = sp.get_sales_achieved(month=m, year=y)

                won_count = Quotation.select().where(
                    ((Quotation.sales_person == sp) | (Quotation.assisted_by == sp)) &
                    (Quotation.status == Quotation.STATUS_WON) &
                    (Quotation.quotation_date >= m_date) &
                    (Quotation.quotation_date <= end_m)
                ).count()

                col_val = 0.0
                pmts = (
                    Payment.select(Payment, Quotation)
                    .join(Quotation)
                    .where(
                        ((Quotation.sales_person == sp) | (Quotation.assisted_by == sp)) &
                        (Payment.payment_date >= m_date) &
                        (Payment.payment_date <= end_m) &
                        (Payment.status == Payment.STATUS_CLEARED)
                    )
                )
                for p in pmts:
                    pq = p.quotation
                    if pq.sales_person_id == sp.id:
                        if getattr(pq, "assisted_by_id", None) and getattr(pq, "split_type", "none") in ("percentage", "amount"):
                            ratio = max(0.0, pq.get_credit_for_salesperson(sp.id) / pq.net_total) if pq.net_total > 0 else 1.0
                            col_val += float(p.amount) * ratio
                        else:
                            col_val += float(p.amount)
                    elif getattr(pq, "assisted_by_id", None) == sp.id:
                        ratio = min(1.0, pq.get_credit_for_salesperson(sp.id) / pq.net_total) if pq.net_total > 0 else 0.0
                        col_val += float(p.amount) * ratio

                variance = achieved - target
                pct = (achieved / target * 100.0) if target > 0 else 0.0
                status = "Achieved" if pct >= 100 else ("Near Target" if pct >= 75 else "Shortfall")

                p_total_target += target
                p_total_achieved += achieved
                p_total_won += won_count
                p_total_col += col_val

                cumulative_map[sp.id]["total_target"] += target
                cumulative_map[sp.id]["total_achieved"] += achieved
                cumulative_map[sp.id]["total_won_count"] += won_count
                cumulative_map[sp.id]["total_collections"] += col_val

                period_reps.append({
                    "sales_person": sp,
                    "name": sp.name,
                    "role": sp.role,
                    "target": round(target, 2),
                    "achieved": round(achieved, 2),
                    "variance": round(variance, 2),
                    "percentage": round(pct, 1),
                    "won_count": won_count,
                    "collections": round(col_val, 2),
                    "status": status,
                })

            p_variance = p_total_achieved - p_total_target
            p_pct = (p_total_achieved / p_total_target * 100.0) if p_total_target > 0 else 0.0

            total_archive_target += p_total_target
            total_archive_achieved += p_total_achieved
            total_archive_collections += p_total_col

            period_archives.append({
                "year": y,
                "month": m,
                "period_label": period_label,
                "start_date": m_date,
                "end_date": end_m,
                "total_target": round(p_total_target, 2),
                "total_achieved": round(p_total_achieved, 2),
                "variance": round(p_variance, 2),
                "percentage": round(p_pct, 1),
                "won_count": p_total_won,
                "collections": round(p_total_col, 2),
                "representatives": period_reps,
            })

        cumulative_list = []
        for sp_id, data in cumulative_map.items():
            tot_t = data["total_target"]
            tot_a = data["total_achieved"]
            var = tot_a - tot_t
            pct = (tot_a / tot_t * 100.0) if tot_t > 0 else 0.0
            cumulative_list.append({
                "sales_person": data["sales_person"],
                "name": data["name"],
                "role": data["role"],
                "total_target": round(tot_t, 2),
                "total_achieved": round(tot_a, 2),
                "variance": round(var, 2),
                "percentage": round(pct, 1),
                "won_count": data["total_won_count"],
                "collections": round(data["total_collections"], 2),
                "status": "Achieved" if pct >= 100 else ("Near Target" if pct >= 75 else "Shortfall"),
            })

        overall_pct = (total_archive_achieved / total_archive_target * 100.0) if total_archive_target > 0 else 0.0

        return {
            "periods": period_archives,
            "cumulative": cumulative_list,
            "total_archive_target": round(total_archive_target, 2),
            "total_archive_achieved": round(total_archive_achieved, 2),
            "total_archive_variance": round(total_archive_achieved - total_archive_target, 2),
            "total_archive_collections": round(total_archive_collections, 2),
            "overall_percentage": round(overall_pct, 1),
            "total_periods_count": len(sorted_periods),
        }

    @staticmethod
    def export_target_archive_csv(output_filepath: str = None) -> str:
        """Exports complete sales target vs achievement archive report to CSV."""
        data = ReportService.get_target_archive_data()
        if not output_filepath:
            output_filepath = str(OUTPUT_PDF_DIR / f"Target_Archive_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["=== SALES TARGET & REVENUE ARCHIVE AUDIT ==="])
            writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Total Historical Periods", data["total_periods_count"]])
            writer.writerow(["Cumulative Target Allocated (INR)", f"{data['total_archive_target']:.2f}"])
            writer.writerow(["Cumulative Won Sales Achieved (INR)", f"{data['total_archive_achieved']:.2f}"])
            writer.writerow(["Cumulative Realized Collections (INR)", f"{data['total_archive_collections']:.2f}"])
            writer.writerow(["Overall Team Target %", f"{data['overall_percentage']:.1f}%"])
            writer.writerow([])
            writer.writerow(["--- PERIOD BY PERIOD ARCHIVE BREAKDOWN ---"])
            writer.writerow(["Period", "Sales Executive", "Role", "Target (INR)", "Achieved (INR)", "Variance (INR)", "% Achieved", "Won Deals Count", "Realized Collections (INR)", "Status"])
            for period in data["periods"]:
                for rep in period["representatives"]:
                    writer.writerow([
                        period["period_label"],
                        rep["name"],
                        rep["role"],
                        f"{rep['target']:.2f}",
                        f"{rep['achieved']:.2f}",
                        f"{rep['variance']:.2f}",
                        f"{rep['percentage']:.1f}%",
                        rep["won_count"],
                        f"{rep['collections']:.2f}",
                        rep["status"],
                    ])
                writer.writerow([
                    f"TOTAL {period['period_label']}",
                    "All Representatives",
                    "Team Aggregate",
                    f"{period['total_target']:.2f}",
                    f"{period['total_achieved']:.2f}",
                    f"{period['variance']:.2f}",
                    f"{period['percentage']:.1f}%",
                    period["won_count"],
                    f"{period['collections']:.2f}",
                    "Team Period Total"
                ])
                writer.writerow([])
            writer.writerow(["--- CUMULATIVE CAREER / YTD ARCHIVE SUMMARY ---"])
            writer.writerow(["Sales Executive", "Role", "Cumulative Target (INR)", "Total Won Sales (INR)", "Net Variance (INR)", "Overall %", "Total Won Deals", "Lifetime Collections (INR)", "Audit Status"])
            for rep in data["cumulative"]:
                writer.writerow([
                    rep["name"],
                    rep["role"],
                    f"{rep['total_target']:.2f}",
                    f"{rep['total_achieved']:.2f}",
                    f"{rep['variance']:.2f}",
                    f"{rep['percentage']:.1f}%",
                    rep["won_count"],
                    f"{rep['collections']:.2f}",
                    rep["status"],
                ])

        return output_filepath

    @staticmethod
    def get_filtered_quotations_data(start_date=None, end_date=None, sales_person_id=None, status=None):
        """Aggregates quotations and summary KPIs based on date range, salesperson, and status filter."""
        from app.services.quotation_service import QuotationService

        quotes = QuotationService.get_all_quotations(
            status=status,
            sales_person_id=sales_person_id,
            start_date=start_date,
            end_date=end_date,
        )

        sp_name = "All Sales Associates"
        if sales_person_id and sales_person_id not in ("All", "all", 0, "0", "All Sales Associates"):
            sp = SalesPerson.get_or_none(SalesPerson.id == sales_person_id)
            if sp:
                sp_name = sp.name

        status_label = status if status and status not in ("All", "all") else "All Statuses"
        if not status_label.startswith("Only ") and status_label in ("Won", "Open", "In-Review", "Lost"):
            status_label = f"Only {status_label}"

        total_count = len(quotes)
        total_net = sum(float(q.net_total or 0.0) for q in quotes)
        total_gross = sum(float(q.gross_total or 0.0) for q in quotes)
        total_tax = sum(float(q.total_tax or 0.0) for q in quotes)
        total_cleared = sum(float(q.get_cleared_payments() or 0.0) for q in quotes)

        won_quotes = [q for q in quotes if q.status == Quotation.STATUS_WON]
        open_quotes = [q for q in quotes if q.status == Quotation.STATUS_OPEN]
        in_review_quotes = [q for q in quotes if q.status == Quotation.STATUS_IN_REVIEW]
        lost_quotes = [q for q in quotes if q.status == Quotation.STATUS_LOST]

        won_total = sum(float(q.net_total or 0.0) for q in won_quotes)
        won_cleared = sum(float(q.get_cleared_payments() or 0.0) for q in won_quotes)
        won_balance = sum(float(q.get_outstanding_balance() or 0.0) for q in won_quotes)
        pipeline_total = sum(float(q.net_total or 0.0) for q in open_quotes + in_review_quotes)
        outstanding_balance = sum(float(q.get_outstanding_balance() or 0.0) for q in quotes)

        # Period label formatting
        if start_date and end_date:
            s_dt = start_date if isinstance(start_date, (date, datetime)) else datetime.strptime(str(start_date), "%Y-%m-%d").date()
            e_dt = end_date if isinstance(end_date, (date, datetime)) else datetime.strptime(str(end_date), "%Y-%m-%d").date()
            period_label = f"{s_dt.strftime('%d %b %Y')} to {e_dt.strftime('%d %b %Y')}"
        elif start_date:
            s_dt = start_date if isinstance(start_date, (date, datetime)) else datetime.strptime(str(start_date), "%Y-%m-%d").date()
            period_label = f"From {s_dt.strftime('%d %b %Y')}"
        elif end_date:
            e_dt = end_date if isinstance(end_date, (date, datetime)) else datetime.strptime(str(end_date), "%Y-%m-%d").date()
            period_label = f"Until {e_dt.strftime('%d %b %Y')}"
        else:
            period_label = "All Time"

        return {
            "quotations": quotes,
            "total_count": total_count,
            "won_count": len(won_quotes),
            "open_count": len(open_quotes),
            "in_review_count": len(in_review_quotes),
            "lost_count": len(lost_quotes),
            "total_net": round(total_net, 2),
            "total_gross": round(total_gross, 2),
            "total_tax": round(total_tax, 2),
            "total_cleared": round(total_cleared, 2),
            "won_total": round(won_total, 2),
            "won_cleared": round(won_cleared, 2),
            "won_balance": round(won_balance, 2),
            "pipeline_total": round(pipeline_total, 2),
            "outstanding_balance": round(outstanding_balance, 2),
            "sales_person_name": sp_name,
            "status_filter": status_label,
            "period_label": period_label,
            "start_date": start_date,
            "end_date": end_date,
        }

    @staticmethod
    def export_quotations_csv(output_filepath: str = None, start_date=None, end_date=None, sales_person_id=None, status=None) -> str:
        """Exports filtered quotations audit report to CSV format."""
        data = ReportService.get_filtered_quotations_data(
            start_date=start_date,
            end_date=end_date,
            sales_person_id=sales_person_id,
            status=status
        )

        status_slug = (data["status_filter"].replace(" ", "_")).replace("-", "_")
        if not output_filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filepath = str(OUTPUT_PDF_DIR / f"Quotations_Report_{status_slug}_{timestamp}.csv")

        with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["=== QUOTATIONS AUDIT REPORT ==="])
            writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Time Period", data["period_label"]])
            writer.writerow(["Sales Executive", data["sales_person_name"]])
            writer.writerow(["Status Filter", data["status_filter"]])
            writer.writerow(["Total Quotations Found", data["total_count"]])
            writer.writerow(["Total Net Value (INR)", f"{data['total_net']:.2f}"])
            writer.writerow(["Won Sales Value (INR)", f"{data['won_total']:.2f}"])
            writer.writerow(["Pipeline Value (INR)", f"{data['pipeline_total']:.2f}"])
            writer.writerow(["Cleared Payments (INR)", f"{data['total_cleared']:.2f}"])
            writer.writerow(["Outstanding Balance (INR)", f"{data['outstanding_balance']:.2f}"])
            writer.writerow([])
            writer.writerow([
                "Sl",
                "Quotation Number",
                "Date",
                "Customer Name",
                "Customer Phone",
                "Delivery / Site Address",
                "Primary Sales Rep",
                "Assisted By",
                "Status",
                "Tax Mode",
                "Taxable Amount (INR)",
                "Total GST (INR)",
                "Gross Total (INR)",
                "Round Off / Disc (INR)",
                "Net Total (INR)",
                "Cleared Payments (INR)",
                "Outstanding Balance (INR)",
            ])

            for idx, q in enumerate(data["quotations"], start=1):
                writer.writerow([
                    idx,
                    q.quotation_number,
                    q.quotation_date.strftime("%Y-%m-%d") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date),
                    q.customer_name,
                    q.customer_phone,
                    q.delivery_address or "",
                    q.sales_person_name,
                    q.assisted_by_name or "-",
                    q.status,
                    getattr(q, "tax_mode", "exclusive"),
                    f"{float(q.taxable_amount or 0.0):.2f}",
                    f"{float(q.total_tax or 0.0):.2f}",
                    f"{float(q.gross_total or 0.0):.2f}",
                    f"{float(q.round_off or 0.0):.2f}",
                    f"{float(q.net_total or 0.0):.2f}",
                    f"{float(q.get_cleared_payments() or 0.0):.2f}",
                    f"{float(q.get_outstanding_balance() or 0.0):.2f}",
                ])

            writer.writerow([
                "TOTAL",
                f"{data['total_count']} Quotes",
                "",
                "",
                "",
                "",
                "",
                "",
                data["status_filter"],
                "",
                f"{sum(float(q.taxable_amount or 0.0) for q in data['quotations']):.2f}",
                f"{data['total_tax']:.2f}",
                f"{data['total_gross']:.2f}",
                f"{sum(float(q.round_off or 0.0) for q in data['quotations']):.2f}",
                f"{data['total_net']:.2f}",
                f"{data['total_cleared']:.2f}",
                f"{data['outstanding_balance']:.2f}",
            ])

        return output_filepath
