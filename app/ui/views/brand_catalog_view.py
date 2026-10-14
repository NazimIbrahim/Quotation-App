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
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Define brands, tile sizes & exact Sqft coverage per box for automated quotation math",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        add_brand_btn = ctk.CTkButton(
            top_bar,
            text="+ Add Tile Brand",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            command=self.open_brand_modal,
            height=36
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
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        left_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        left_header = ctk.CTkFrame(left_card, fg_color="transparent")
        left_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            left_header,
            text="🏷️ Brands Master",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            left_card,
            placeholder_text="Search brands...",
            height=34,
            corner_radius=Theme.RADIUS_PILL,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            font=ctk.CTkFont(size=11)
        )
        self.search_entry.pack(fill="x", padx=16, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        self.brands_scroll = ctk.CTkScrollableFrame(left_card, fg_color="transparent")
        self.brands_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Right Column: Brand Sizes & Box Coverage Card
        self.right_card = ctk.CTkFrame(
            main_split,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
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
            card_bg = (Theme.PRIMARY, "#B83222") if is_active else Theme.BTN_SECONDARY_BG
            text_color = "white" if is_active else (Theme.BLACK, Theme.PAPER)
            border_col = Theme.BTN_PRIMARY_BORDER if is_active else Theme.BTN_SECONDARY_BORDER

            sizes_count = b.size_coverages.count()

            btn = ctk.CTkButton(
                self.brands_scroll,
                text=f"{b.name}\n{sizes_count} Sizes & Coverages Configured",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=text_color,
                fg_color=card_bg,
                hover_color=Theme.PRIMARY_HOVER if is_active else Theme.BTN_SECONDARY_HOVER,
                corner_radius=Theme.RADIUS_BUTTON,
                border_width=1,
                border_color=border_col,
                anchor="w",
                height=48,
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
            text_color=("#615D56", "#A8A297")
        ).pack(anchor="w")

        act_box = ctk.CTkFrame(header_row, fg_color="transparent")
        act_box.pack(side="right")

        add_size_btn = ctk.CTkButton(
            act_box,
            text="+ Add Size & Coverage",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SUCCESS_BORDER,
            command=self.open_size_modal,
            height=30
        )
        add_size_btn.pack(side="left", padx=4)

        edit_b_btn = ctk.CTkButton(
            act_box,
            text="✏️ Edit",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=70,
            height=30,
            corner_radius=Theme.RADIUS_PILL,
            fg_color=Theme.BTN_SECONDARY_BG,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_SECONDARY_BORDER,
            text_color=(Theme.BLACK, Theme.PAPER),
            command=lambda: self.open_brand_modal(b)
        )
        edit_b_btn.pack(side="left", padx=4)

        del_b_btn = ctk.CTkButton(
            act_box,
            text="🗑️",
            font=ctk.CTkFont(size=11),
            width=34,
            height=30,
            corner_radius=Theme.RADIUS_PILL,
            border_width=1,
            border_color=Theme.BTN_DANGER_BORDER,
            fg_color="transparent",
            text_color=Theme.DANGER,
            command=lambda: self.delete_brand(b)
        )
        del_b_btn.pack(side="left")

        # Table Header Row (Stone)
        h_frame = ctk.CTkFrame(self.brand_detail_container, fg_color=(Theme.STONE, "#242220"), height=36, corner_radius=10)
        h_frame.pack(fill="x", padx=(6, 23), pady=(6, 4))
        weights = [2, 2, 3, 2, 2, 2, 2]
        for idx, w in enumerate(weights):
            h_frame.grid_columnconfigure(idx, weight=w, uniform="brand_sizes")

        cols = ["TILE / ITEM SIZE", "TYPE", "COVERAGE (SQFT/BOX)", "PCS / BOX", "RATE / SQFT", "UNIT / BOX PRICE", "ACTIONS"]
        for idx, text in enumerate(cols):
            ctk.CTkLabel(
                h_frame,
                text=text,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER),
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
                text_color=("#615D56", "#A8A297")
            ).pack(pady=30)
            return

        for sc in size_entries:
            rf = ctk.CTkFrame(rows_scroll, fg_color=("#FAF8F5", "#181615"), corner_radius=8)
            rf.pack(fill="x", pady=2)
            for idx, w in enumerate(weights):
                rf.grid_columnconfigure(idx, weight=w, uniform="brand_sizes")

            ptype = getattr(sc, "product_type", "Box") or "Box"
            type_color = Theme.PRIMARY if ptype == "Box" else (Theme.SUCCESS if ptype == "Sqft" else Theme.SECONDARY)

            # Col 0: Size
            ctk.CTkLabel(
                rf,
                text=sc.size,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).grid(row=0, column=0, padx=8, pady=6, sticky="w")

            # Col 1: Product Type
            ctk.CTkLabel(
                rf,
                text=ptype,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=type_color
            ).grid(row=0, column=1, padx=8, pady=6, sticky="w")

            # Col 2: Coverage
            cov_txt = f"{sc.coverage_sqft:.2f} Sqft" if ptype == "Box" else "—"
            ctk.CTkLabel(
                rf,
                text=cov_txt,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold" if ptype == "Box" else "normal"),
                text_color=Theme.PRIMARY if ptype == "Box" else ("#615D56", "#A8A297")
            ).grid(row=0, column=2, padx=8, pady=6, sticky="w")

            # Col 3: Pcs / box
            pcs_txt = f"{sc.pieces_per_box} pcs" if ptype == "Box" else "—"
            ctk.CTkLabel(
                rf,
                text=pcs_txt,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=("#615D56", "#A8A297")
            ).grid(row=0, column=3, padx=8, pady=6, sticky="w")

            # Col 4: Rate per Sqft
            r_sqft_txt = f"₹ {sc.default_rate_sqft:,.2f}" if (ptype in ("Box", "Sqft") and sc.default_rate_sqft > 0) else "—"
            ctk.CTkLabel(
                rf,
                text=r_sqft_txt,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).grid(row=0, column=4, padx=8, pady=6, sticky="w")

            # Col 5: Unit / Box Price
            unit_suffix = "/Bx" if ptype == "Box" else (f"/{ptype[:3]}" if ptype != "Sqft" else "/Sqft")
            box_txt = f"₹ {sc.default_rate_box:,.2f} {unit_suffix}" if sc.default_rate_box > 0 else (
                f"₹ {sc.default_rate_sqft:,.2f} /Sqft" if (ptype == "Sqft" and sc.default_rate_sqft > 0) else "—"
            )
            ctk.CTkLabel(
                rf,
                text=box_txt,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=Theme.SUCCESS
            ).grid(row=0, column=5, padx=8, pady=6, sticky="w")

            # Col 6: Actions
            act_f = ctk.CTkFrame(rf, fg_color="transparent")
            act_f.grid(row=0, column=6, padx=8, pady=4, sticky="w")

            ctk.CTkButton(
                act_f,
                text="Edit",
                width=48,
                height=24,
                corner_radius=Theme.RADIUS_PILL,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=Theme.BTN_SECONDARY_BG,
                hover_color=Theme.BTN_SECONDARY_HOVER,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                text_color=(Theme.BLACK, Theme.PAPER),
                command=lambda item=sc: self.open_size_modal(item)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_f,
                text="✕",
                width=26,
                height=24,
                corner_radius=Theme.RADIUS_PILL,
                font=ctk.CTkFont(size=10, weight="bold"),
                border_width=Theme.BORDER_WIDTH_BUTTON,
                fg_color=Theme.BTN_SECONDARY_BG,
                hover_color=Theme.DANGER,
                text_color=Theme.DANGER,
                command=lambda item=sc: self.delete_size(item)
            ).pack(side="left", padx=2)

        # Bottom spacer so last row is never cut off
        ctk.CTkFrame(rows_scroll, height=14, fg_color="transparent").pack(fill="x")

    def open_brand_modal(self, brand=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Brand" if brand else "Add Tile Brand")
        dialog.geometry("440x300")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tile Brand Master", font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(f, text="Brand Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        name_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. Kajaria Eternity / Simpolo"
        )
        if brand:
            name_ent.insert(0, brand.name)
        name_ent.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(f, text="Brand Description / Grade:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        desc_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. Premium Vitrified Slabs & Surfaces"
        )
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
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            height=36,
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
        dialog.geometry("480x550")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tile Size & Box Coverage Spec", font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold")).pack(pady=(16, 10))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        # 0. Product Type / Unit
        ctk.CTkLabel(f, text="Product Type / Unit:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        init_ptype = getattr(size_entry, "product_type", "Box") if size_entry else "Box"
        if not init_ptype:
            init_ptype = "Box"

        ptype_menu = ctk.CTkOptionMenu(
            f,
            values=["Box", "Pieces", "Sqft", "Bags", "Nos"],
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.BTN_SECONDARY_BG,
            button_color=Theme.PRIMARY,
            button_hover_color=Theme.PRIMARY_HOVER,
            text_color=(Theme.BLACK, Theme.PAPER),
            font=ctk.CTkFont(size=11, weight="bold")
        )
        ptype_menu.set(init_ptype)
        ptype_menu.pack(fill="x", pady=(2, 6))

        # 1. Tile Size / Item Spec
        size_lbl = ctk.CTkLabel(f, text="Item / Tile Size:", font=ctk.CTkFont(size=11, weight="bold"))
        size_lbl.pack(anchor="w")
        all_existing_sizes = []
        try:
            for s in BrandSizeCoverage.select(BrandSizeCoverage.size).distinct():
                sz_name = s.size.strip()
                if sz_name and sz_name not in all_existing_sizes:
                    all_existing_sizes.append(sz_name)
        except Exception:
            pass
        combined_sizes = all_existing_sizes + [s for s in COMMON_TILE_SIZES if s not in all_existing_sizes]
        size_combo = ctk.CTkComboBox(
            f,
            values=combined_sizes,
            height=34,
            corner_radius=Theme.RADIUS_INPUT
        )
        if size_entry:
            size_combo.set(size_entry.size)
        size_combo.pack(fill="x", pady=(2, 6))

        # 2. Pieces per box
        pcs_lbl = ctk.CTkLabel(f, text="Pieces Per Box:", font=ctk.CTkFont(size=11, weight="bold"))
        pcs_lbl.pack(anchor="w")
        pcs_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. 2"
        )
        pcs_ent.insert(0, str(size_entry.pieces_per_box) if size_entry else "2")
        pcs_ent.pack(fill="x", pady=(2, 6))

        # 3. Coverage Area in Sqft
        cov_lbl = ctk.CTkLabel(f, text="Coverage Area in Sqft Per Box:", font=ctk.CTkFont(size=11, weight="bold"))
        cov_lbl.pack(anchor="w")
        cov_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. 15.50 or 23.25"
        )
        cov_ent.insert(0, f"{size_entry.coverage_sqft:.2f}" if size_entry else "15.50")
        cov_ent.pack(fill="x", pady=(2, 6))

        # 4. Default Rate per Sqft
        r_sqft_lbl = ctk.CTkLabel(f, text="Default Rate Per Sqft (₹):", font=ctk.CTkFont(size=11, weight="bold"))
        r_sqft_lbl.pack(anchor="w")
        rate_sqft_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. 110.00"
        )
        rate_sqft_ent.insert(0, f"{size_entry.default_rate_sqft:.2f}" if (size_entry and size_entry.default_rate_sqft > 0) else "")
        rate_sqft_ent.pack(fill="x", pady=(2, 6))

        # 5. Default Unit / Box Price
        r_box_lbl = ctk.CTkLabel(f, text="Default Box Price (₹) (Auto-calculated):", font=ctk.CTkFont(size=11, weight="bold"))
        r_box_lbl.pack(anchor="w")
        rate_box_ent = ctk.CTkEntry(
            f,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.INSET_BG,
            border_color=Theme.INSET_BORDER,
            border_width=Theme.BORDER_WIDTH_INPUT,
            placeholder_text="e.g. 1705.00"
        )
        rate_box_ent.insert(0, f"{size_entry.default_rate_box:.2f}" if (size_entry and size_entry.default_rate_box > 0) else "")
        rate_box_ent.pack(fill="x", pady=(2, 10))

        def on_modal_ptype_changed(val):
            if val == "Box":
                cov_lbl.configure(text="Coverage Area in Sqft Per Box:")
                pcs_lbl.configure(text="Pieces Per Box:")
                r_sqft_lbl.configure(text="Default Rate Per Sqft (₹):")
                r_box_lbl.configure(text="Default Box Price (₹) (Auto-calculated):")
            elif val == "Sqft":
                cov_lbl.configure(text="Coverage Area (Not required for Sqft):")
                pcs_lbl.configure(text="Pieces (Not required for Sqft):")
                r_sqft_lbl.configure(text="Default Rate Per Sqft (₹):")
                r_box_lbl.configure(text="Optional Unit Price (₹):")
            elif val == "Pieces":
                cov_lbl.configure(text="Coverage Area (Not required for Pieces):")
                pcs_lbl.configure(text="Pieces Per Unit (Default: 1):")
                r_sqft_lbl.configure(text="Rate / Sqft (Optional):")
                r_box_lbl.configure(text="Default Rate Per Piece (₹):")
            elif val == "Bags":
                cov_lbl.configure(text="Coverage Area (Not required for Bags):")
                pcs_lbl.configure(text="Units (Default: 1):")
                r_sqft_lbl.configure(text="Rate / Sqft (Optional):")
                r_box_lbl.configure(text="Default Rate Per Bag (₹):")
            elif val == "Nos":
                cov_lbl.configure(text="Coverage Area (Not required for Nos):")
                pcs_lbl.configure(text="Units (Default: 1):")
                r_sqft_lbl.configure(text="Rate / Sqft (Optional):")
                r_box_lbl.configure(text="Default Rate Per No (₹):")

        ptype_menu.configure(command=on_modal_ptype_changed)
        on_modal_ptype_changed(init_ptype)

        def auto_calc_box(e=None):
            try:
                curr_type = ptype_menu.get().strip()
                if curr_type == "Box":
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
            chosen_type = ptype_menu.get().strip()
            try:
                pcs = int(pcs_ent.get().strip() or 1)
                cov = float(cov_ent.get().strip() or (15.5 if chosen_type == "Box" else 1.0))
                r_sqft = float(rate_sqft_ent.get().strip() or 0.0)
                r_box = float(rate_box_ent.get().strip() or 0.0)
                if chosen_type == "Box" and r_box <= 0 and r_sqft > 0 and cov > 0:
                    r_box = round(r_sqft * cov, 2)
            except ValueError:
                msgbox.showerror("Error", "Please enter valid numeric values.", parent=dialog)
                return

            if not sz:
                msgbox.showwarning("Notice", "Size / item specification is required.", parent=dialog)
                return

            if size_entry:
                size_entry.size = sz
                size_entry.product_type = chosen_type
                size_entry.pieces_per_box = pcs
                size_entry.coverage_sqft = cov
                size_entry.default_rate_sqft = r_sqft
                size_entry.default_rate_box = r_box
                size_entry.save()
            else:
                BrandSizeCoverage.create(
                    brand=self.selected_brand,
                    size=sz,
                    product_type=chosen_type,
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
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            border_color=Theme.BTN_PRIMARY_BORDER,
            height=36,
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
