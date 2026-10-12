"""
Brand & Coverage Master Catalog View: Manage tile brands,
standard tile sizes, and exact box coverage areas (Sqft per box).
"""
import tkinter.messagebox as msgbox
import customtkinter as ctk

from app.ui.theme import Theme
from app.config import COMMON_TILE_SIZES
from app.database.models import TileBrand, BrandSizeCoverage


class BrandCatalogView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.selected_brand = None

        self.build_ui()
        self.load_brands()

    def build_ui(self):
        # 1. Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Tile Brands & Box Coverage Catalog",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Define brands, tile sizes & exact Sqft coverage per box for automated quotation math",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#64748B", "#94A3B8"),
        )
        subtitle.pack(anchor="w")

        add_brand_btn = ctk.CTkButton(
            top_bar,
            text="+ Add Tile Brand",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.open_brand_modal,
            height=34
        )
        add_brand_btn.pack(side="right")

        # 2. Main Two-Column Layout (Left: Brands List, Right: Sizes & Coverages)
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        main_split.grid_columnconfigure(0, weight=2)
        main_split.grid_columnconfigure(1, weight=4)

        # Left Column: Brands Directory Card
        left_card = ctk.CTkFrame(
            main_split,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        left_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        left_header = ctk.CTkFrame(left_card, fg_color="transparent")
        left_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            left_header,
            text="🏷️ Brands Master",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            left_card,
            placeholder_text="Search brands...",
            height=30,
            font=ctk.CTkFont(size=11)
        )
        self.search_entry.pack(fill="x", padx=16, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        self.brands_scroll = ctk.CTkScrollableFrame(left_card, fg_color="transparent")
        self.brands_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Right Column: Brand Sizes & Box Coverage Card
        self.right_card = ctk.CTkFrame(
            main_split,
            corner_radius=12,
            fg_color=("white", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.right_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        self.brand_detail_container = ctk.CTkFrame(self.right_card, fg_color="transparent")
        self.brand_detail_container.pack(fill="both", expand=True, padx=16, pady=16)

    def _on_search_key(self, event=None):
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(200, self.load_brands)

    def load_brands(self):
        for widget in self.brands_scroll.winfo_children():
            widget.destroy()

        q_txt = self.search_entry.get().strip()
        query = TileBrand.select().order_by(TileBrand.name)
        if q_txt:
            query = query.where(TileBrand.name.ilike(f"%{q_txt}%"))

        brands = list(query)
        if not brands:
            ctk.CTkLabel(self.brands_scroll, text="No brands found.").pack(pady=20)
            return

        for b in brands:
            is_active = self.selected_brand and self.selected_brand.id == b.id
            card_bg = (Theme.PRIMARY, "#0284C7") if is_active else ("#F8FAFC", "#0F172A")
            text_color = "white" if is_active else ("#0F172A", "#F8FAFC")

            sizes_count = b.size_coverages.count()

            btn = ctk.CTkButton(
                self.brands_scroll,
                text=f"{b.name}\n{sizes_count} Sizes & Coverages Configured",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=text_color,
                fg_color=card_bg,
                hover_color=Theme.PRIMARY_HOVER,
                corner_radius=8,
                anchor="w",
                height=46,
                command=lambda brand=b: self.select_brand(brand)
            )
            btn.pack(fill="x", pady=3)

        if not self.selected_brand and brands:
            self.select_brand(brands[0])

    def select_brand(self, brand: TileBrand):
        self.selected_brand = brand
        self.render_brand_detail()

    def render_brand_detail(self):
        for widget in self.brand_detail_container.winfo_children():
            widget.destroy()

        if not self.selected_brand:
            ctk.CTkLabel(self.brand_detail_container, text="Select a brand from the left.").pack(pady=40)
            return

        b = self.selected_brand

        # Header with Brand Name and Actions
        header_row = ctk.CTkFrame(self.brand_detail_container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))

        title_box = ctk.CTkFrame(header_row, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=f"✦ {b.name}",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=20, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(anchor="w")

        desc_txt = b.description or "Standard vitrified tile manufacturer"
        ctk.CTkLabel(
            title_box,
            text=desc_txt,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color=("#64748B", "#94A3B8")
        ).pack(anchor="w")

        act_box = ctk.CTkFrame(header_row, fg_color="transparent")
        act_box.pack(side="right")

        add_size_btn = ctk.CTkButton(
            act_box,
            text="+ Add Size & Coverage",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=self.open_size_modal,
            height=28
        )
        add_size_btn.pack(side="left", padx=4)

        edit_b_btn = ctk.CTkButton(
            act_box,
            text="✏️ Edit",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=60,
            height=28,
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            command=lambda: self.open_brand_modal(b)
        )
        edit_b_btn.pack(side="left", padx=4)

        del_b_btn = ctk.CTkButton(
            act_box,
            text="🗑️",
            font=ctk.CTkFont(size=11),
            width=32,
            height=28,
            fg_color="transparent",
            text_color=Theme.DANGER,
            command=lambda: self.delete_brand(b)
        )
        del_b_btn.pack(side="left")

        # Table Header Row
        h_frame = ctk.CTkFrame(self.brand_detail_container, fg_color=("#F1F5F9", "#0F172A"), height=32, corner_radius=6)
        h_frame.pack(fill="x", pady=(6, 4))
        h_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        cols = ["TILE SIZE", "COVERAGE (SQFT/BOX)", "PCS / BOX", "RATE / SQFT", "BOX PRICE (₹)", "ACTIONS"]
        for idx, text in enumerate(cols):
            ctk.CTkLabel(
                h_frame,
                text=text,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                text_color=("#475569", "#94A3B8"),
                anchor="w"
            ).grid(row=0, column=idx, padx=8, pady=6, sticky="w")

        # Table Scrollable Rows
        rows_scroll = ctk.CTkScrollableFrame(self.brand_detail_container, fg_color="transparent")
        rows_scroll.pack(fill="both", expand=True)

        size_entries = list(b.size_coverages.order_by(BrandSizeCoverage.size))
        if not size_entries:
            ctk.CTkLabel(
                rows_scroll,
                text="No sizes configured for this brand yet. Click '+ Add Size & Coverage' to configure.",
                font=ctk.CTkFont(size=12),
                text_color=("#64748B", "#94A3B8")
            ).pack(pady=30)
            return

        for sc in size_entries:
            rf = ctk.CTkFrame(rows_scroll, fg_color=("#F8FAFC", "#0F172A"), corner_radius=6)
            rf.pack(fill="x", pady=2)
            rf.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

            # Col 0: Size
            ctk.CTkLabel(
                rf,
                text=sc.size,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
                text_color=("#0F172A", "#F8FAFC")
            ).grid(row=0, column=0, padx=8, pady=6, sticky="w")

            # Col 1: Coverage
            ctk.CTkLabel(
                rf,
                text=f"{sc.coverage_sqft:.2f} Sqft",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
                text_color=Theme.ACCENT_GOLD
            ).grid(row=0, column=1, padx=8, pady=6, sticky="w")

            # Col 2: Pcs / box
            ctk.CTkLabel(
                rf,
                text=f"{sc.pieces_per_box} pcs",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=("#64748B", "#94A3B8")
            ).grid(row=0, column=2, padx=8, pady=6, sticky="w")

            # Col 3: Rate per Sqft
            ctk.CTkLabel(
                rf,
                text=f"₹ {sc.default_rate_sqft:,.2f}" if sc.default_rate_sqft > 0 else "-",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
            ).grid(row=0, column=3, padx=8, pady=6, sticky="w")

            # Col 4: Box Price
            ctk.CTkLabel(
                rf,
                text=f"₹ {sc.default_rate_box:,.2f}" if sc.default_rate_box > 0 else "-",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=Theme.SUCCESS
            ).grid(row=0, column=4, padx=8, pady=6, sticky="w")

            # Col 5: Actions
            act_f = ctk.CTkFrame(rf, fg_color="transparent")
            act_f.grid(row=0, column=5, padx=8, pady=4, sticky="w")

            ctk.CTkButton(
                act_f,
                text="Edit",
                width=45,
                height=22,
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=("#E2E8F0", "#334155"),
                text_color=("#0F172A", "#F8FAFC"),
                command=lambda item=sc: self.open_size_modal(item)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_f,
                text="✕",
                width=24,
                height=22,
                font=ctk.CTkFont(size=9),
                fg_color="transparent",
                text_color=Theme.DANGER,
                command=lambda item=sc: self.delete_size(item)
            ).pack(side="left", padx=2)

    def open_brand_modal(self, brand=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Brand" if brand else "Add Tile Brand")
        dialog.geometry("420x280")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tile Brand Master", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(f, text="Brand Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        name_ent = ctk.CTkEntry(f, placeholder_text="e.g. Kajaria Eternity / Simpolo")
        if brand:
            name_ent.insert(0, brand.name)
        name_ent.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(f, text="Brand Description / Grade:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        desc_ent = ctk.CTkEntry(f, placeholder_text="e.g. Premium Vitrified Slabs & Surfaces")
        if brand and brand.description:
            desc_ent.insert(0, brand.description)
        desc_ent.pack(fill="x", pady=(2, 14))

        def save_b():
            n = name_ent.get().strip()
            d = desc_ent.get().strip()
            if not n:
                msgbox.showwarning("Incomplete", "Brand name is required.", parent=dialog)
                return
            if brand:
                brand.name = n
                brand.description = d or None
                brand.save()
            else:
                new_b = TileBrand.create(name=n, description=d or None)
                self.selected_brand = new_b
            dialog.destroy()
            try:
                from app.ui.views.quotation_editor_view import ItemRowWidget
                ItemRowWidget.invalidate_catalog_cache()
            except Exception:
                pass
            self.load_brands()
            self.render_brand_detail()

        ctk.CTkButton(
            dialog,
            text="Save Brand",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=save_b
        ).pack(pady=(0, 20))

    def delete_brand(self, brand: TileBrand):
        confirm = msgbox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete brand '{brand.name}' and all its configured sizes?"
        )
        if confirm:
            brand.delete_instance(recursive=True)
            self.selected_brand = None
            try:
                from app.ui.views.quotation_editor_view import ItemRowWidget
                ItemRowWidget.invalidate_catalog_cache()
            except Exception:
                pass
            self.load_brands()
            self.render_brand_detail()

    def open_size_modal(self, size_entry=None):
        if not self.selected_brand:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Size & Coverage" if size_entry else f"Add Size to {self.selected_brand.name}")
        dialog.geometry("450x420")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tile Size & Box Coverage Spec", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        # Tile Size
        ctk.CTkLabel(f, text="Tile Size:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        all_existing_sizes = []
        try:
            for s in BrandSizeCoverage.select(BrandSizeCoverage.size).distinct():
                sz_name = s.size.strip()
                if sz_name and sz_name not in all_existing_sizes:
                    all_existing_sizes.append(sz_name)
        except Exception:
            pass
        combined_sizes = all_existing_sizes + [s for s in COMMON_TILE_SIZES if s not in all_existing_sizes]
        size_combo = ctk.CTkComboBox(f, values=combined_sizes)
        if size_entry:
            size_combo.set(size_entry.size)
        size_combo.pack(fill="x", pady=(2, 6))

        # Pieces per box
        ctk.CTkLabel(f, text="Pieces Per Box:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        pcs_ent = ctk.CTkEntry(f, placeholder_text="e.g. 2")
        pcs_ent.insert(0, str(size_entry.pieces_per_box) if size_entry else "2")
        pcs_ent.pack(fill="x", pady=(2, 6))

        # Coverage Area in Sqft
        ctk.CTkLabel(f, text="Coverage Area in Sqft Per Box:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        cov_ent = ctk.CTkEntry(f, placeholder_text="e.g. 15.50 or 23.25")
        cov_ent.insert(0, f"{size_entry.coverage_sqft:.2f}" if size_entry else "15.50")
        cov_ent.pack(fill="x", pady=(2, 6))

        # Default Rate per Sqft
        ctk.CTkLabel(f, text="Default Rate Per Sqft (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        rate_sqft_ent = ctk.CTkEntry(f, placeholder_text="e.g. 110.00")
        rate_sqft_ent.insert(0, f"{size_entry.default_rate_sqft:.2f}" if (size_entry and size_entry.default_rate_sqft > 0) else "")
        rate_sqft_ent.pack(fill="x", pady=(2, 6))

        # Default Box Price
        ctk.CTkLabel(f, text="Default Box Price (₹) (Auto-calculated):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        rate_box_ent = ctk.CTkEntry(f, placeholder_text="e.g. 1705.00")
        rate_box_ent.insert(0, f"{size_entry.default_rate_box:.2f}" if (size_entry and size_entry.default_rate_box > 0) else "")
        rate_box_ent.pack(fill="x", pady=(2, 12))

        def auto_calc_box(e=None):
            try:
                cov = float(cov_ent.get().strip() or 0.0)
                r_sqft = float(rate_sqft_ent.get().strip() or 0.0)
                if cov > 0 and r_sqft > 0:
                    box_p = round(cov * r_sqft, 2)
                    rate_box_ent.delete(0, "end")
                    rate_box_ent.insert(0, f"{box_p:.2f}")
            except Exception:
                pass

        rate_sqft_ent.bind("<KeyRelease>", auto_calc_box)
        cov_ent.bind("<KeyRelease>", auto_calc_box)

        def save_sz():
            sz = size_combo.get().strip()
            try:
                pcs = int(pcs_ent.get().strip() or 2)
                cov = float(cov_ent.get().strip() or 15.5)
                r_sqft = float(rate_sqft_ent.get().strip() or 0.0)
                r_box = float(rate_box_ent.get().strip() or 0.0)
                if r_box <= 0 and r_sqft > 0 and cov > 0:
                    r_box = round(r_sqft * cov, 2)
            except ValueError:
                msgbox.showerror("Error", "Please enter valid numeric values.", parent=dialog)
                return

            if not sz:
                msgbox.showwarning("Notice", "Size is required.", parent=dialog)
                return

            if size_entry:
                size_entry.size = sz
                size_entry.pieces_per_box = pcs
                size_entry.coverage_sqft = cov
                size_entry.default_rate_sqft = r_sqft
                size_entry.default_rate_box = r_box
                size_entry.save()
            else:
                BrandSizeCoverage.create(
                    brand=self.selected_brand,
                    size=sz,
                    pieces_per_box=pcs,
                    coverage_sqft=cov,
                    default_rate_sqft=r_sqft,
                    default_rate_box=r_box
                )

            dialog.destroy()
            try:
                from app.ui.views.quotation_editor_view import ItemRowWidget
                ItemRowWidget.invalidate_catalog_cache()
            except Exception:
                pass
            self.load_brands()
            self.render_brand_detail()

        ctk.CTkButton(
            dialog,
            text="Save Size & Coverage",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=save_sz
        ).pack(pady=(0, 20))

    def delete_size(self, item: BrandSizeCoverage):
        confirm = msgbox.askyesno("Confirm Delete", f"Delete size '{item.size}' from {item.brand.name}?")
        if confirm:
            item.delete_instance()
            try:
                from app.ui.views.quotation_editor_view import ItemRowWidget
                ItemRowWidget.invalidate_catalog_cache()
            except Exception:
                pass
            self.render_brand_detail()
            self.load_brands()
