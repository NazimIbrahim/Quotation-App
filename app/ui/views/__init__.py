"""Views package initialization."""
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.quotation_list_view import QuotationListView
from app.ui.views.quotation_editor_view import QuotationEditorView
from app.ui.views.payment_view import PaymentTrackingView
from app.ui.views.customer_view import CustomerManagementView
from app.ui.views.sales_team_view import SalesTeamView
from app.ui.views.reports_view import ReportsView
from app.ui.views.settings_view import CompanySettingsView
from app.ui.views.brand_catalog_view import BrandCatalogView


__all__ = [
    "DashboardView",
    "QuotationListView",
    "QuotationEditorView",
    "PaymentTrackingView",
    "CustomerManagementView",
    "SalesTeamView",
    "ReportsView",
    "CompanySettingsView",
    "BrandCatalogView",
]

