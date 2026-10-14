"""
Quotation Editor View: Interactive builder for creating and editing
multi-area ceramic quotations with automatic calculations.
"""
from datetime import date, datetime
import tkinter.messagebox as msgbox
import customtkinter as ctk

from app.ui.theme import Theme
from app.config import DEFAULT_PROJECT_AREAS, COMMON_TILE_SIZES
from app.database.models import Customer, SalesPerson, Quotation, TileBrand, BrandSizeCoverage
from app.services.quotation_service import QuotationService
from app.services.pdf_service import CeramicPDFGenerator


class ItemRowWidget(ctk.CTkFrame):
    """Single row representing a tile item within an area section with Brand and Coverage Area."""
    def __init__(self, master, on_recalc, sl_no=1, data=None, on_delete=None, catalog_context=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_recalc = on_recalc
        self.on_delete = on_delete
        self.sl_no = sl_no
        self.catalog_context = catalog_context or {}
        self._is_updating = False

        data = data or {}

        # 12 columns in grid:
        # 0: Sl (weight 1)
        # 1: Description (weight 5)
        # 2: Size (weight 2)
        # 3: Brand (weight 3)
        # 4: Coverage Area (Sqft/Box) (weight 2)
        # 5: Qty Sqft (weight 2)
        # 6: Rate Sqft (weight 2)
        # 7: Tax Mode (18%) (weight 2)
        # 8: Qty Box (weight 2)
        # 9: Rate Box (weight 2)
        # 10: Total Amount (weight 2)
        # 11: Delete (weight 1)
        item_col_weights = [1, 5, 2, 3, 2, 2, 2, 2, 2, 2, 2, 1]
        for idx, w in enumerate(item_col_weights):
            self.grid_columnconfigure(idx, weight=w, uniform="area_item_cols")

        # 0. Sl. No
        self.sl_label = ctk.CTkLabel(
            self,
            text=str(sl_no),
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            width=24
        )
        self.sl_label.grid(row=0, column=0, padx=2, pady=3)

        # 1. Description
        self.desc_entry = ctk.CTkEntry(
            self,
            placeholder_text="e.g. OMBRA EMERALD ULTRA-SS",
            height=28,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        self.desc_entry.insert(0, data.get("description", ""))
        self.desc_entry.grid(row=0, column=1, padx=2, pady=3, sticky="ew")
        self.desc_entry.bind("<KeyRelease>", lambda e: self.on_recalc())

        # Determine initial brand directly from active brands in DB
        brand_names = self.get_active_brands_from_db()
        initial_brand = data.get("brand") or (brand_names[0] if brand_names else "")

        # Compute BRAND-WISE SIZES ONLY from database
        initial_sizes = self.get_sizes_for_brand(initial_brand)
        initial_size = data.get("size")
        if not initial_size:
            genuine = [s for s in initial_sizes if not s.startswith("+ Add")]
            initial_size = genuine[0] if genuine else (initial_sizes[0] if initial_sizes else "")

        # 2. Size Combo (Brand-wise sizes only)
        self.size_combo = ctk.CTkComboBox(
            self,
            values=initial_sizes,
            height=28,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            command=self.on_size_selected
        )
        self.size_combo.set(initial_size)
        self.size_combo.grid(row=0, column=2, padx=2, pady=3, sticky="ew")

        # 3. Brand Combo
        self.brand_combo = ctk.CTkComboBox(
            self,
            values=brand_names,
            height=28,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            command=self.on_brand_selected
        )
        self.brand_combo.set(initial_brand)
        self.brand_combo.grid(row=0, column=3, padx=2, pady=3, sticky="ew")

        # Hook dropdown menus so they auto-query fresh database records on every click
        self._setup_dynamic_dropdown_auto_refresh()

        # 4. Coverage Area (Sqft/Box) Entry
        self.cov_entry = ctk.CTkEntry(
            self,
            placeholder_text="Sqft/Bx",
            height=28,
            width=65,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("coverage_area"):
            self.cov_entry.insert(0, f"{float(data['coverage_area']):g}")
        self.cov_entry.grid(row=0, column=4, padx=2, pady=3, sticky="ew")
        self.cov_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("cov"))

        # 5. Quantity in Sqft
        self.sqft_entry = ctk.CTkEntry(
            self,
            placeholder_text="Sqft",
            height=28,
            width=60,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("quantity_sqft"):
            self.sqft_entry.insert(0, str(data["quantity_sqft"]))
        self.sqft_entry.grid(row=0, column=5, padx=2, pady=3, sticky="ew")
        self.sqft_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("sqft"))

        # 6. Rate per Sqft
        self.rate_sqft_entry = ctk.CTkEntry(
            self,
            placeholder_text="₹/Sqft",
            height=28,
            width=60,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("rate_per_sqft"):
            self.rate_sqft_entry.insert(0, str(data["rate_per_sqft"]))
        self.rate_sqft_entry.grid(row=0, column=6, padx=2, pady=3, sticky="ew")
        self.rate_sqft_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("rate_sqft"))

        # 7. Tax Mode (18%) Option
        init_tax_mode = data.get("tax_mode", "exclusive")
        tax_str = "Incl. 18%" if init_tax_mode == "inclusive" else "Excl. 18%"
        self.tax_combo = ctk.CTkOptionMenu(
            self,
            values=["Excl. 18%", "Incl. 18%"],
            height=28,
            width=82,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
            fg_color=(Theme.STONE, "#2B2824"),
            text_color=(Theme.BLACK, Theme.PAPER),
            button_color=Theme.PRIMARY,
            button_hover_color=Theme.PRIMARY_HOVER,
            dropdown_fg_color=(Theme.PAPER, "#201E1C"),
            dropdown_text_color=(Theme.BLACK, Theme.PAPER),
            dropdown_hover_color=(Theme.STONE, "#332F2A"),
            command=self.on_tax_mode_changed
        )
        self.tax_combo.set(tax_str)
        self.tax_combo.grid(row=0, column=7, padx=2, pady=3, sticky="ew")

        # 8. Quantity in Boxes
        self.box_entry = ctk.CTkEntry(
            self,
            placeholder_text="Boxes",
            height=28,
            width=60,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("quantity_boxes"):
            self.box_entry.insert(0, str(data["quantity_boxes"]))
        self.box_entry.grid(row=0, column=8, padx=2, pady=3, sticky="ew")
        self.box_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("box"))

        # 9. Rate per Box
        self.rate_box_entry = ctk.CTkEntry(
            self,
            placeholder_text="₹/Box",
            height=28,
            width=60,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("rate_per_box"):
            self.rate_box_entry.insert(0, str(data["rate_per_box"]))
        self.rate_box_entry.grid(row=0, column=9, padx=2, pady=3, sticky="ew")
        self.rate_box_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("rate_box"))

        # 10. Total Amount Entry
        self.total_entry = ctk.CTkEntry(
            self,
            placeholder_text="Total ₹",
            height=28,
            width=75,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        if data.get("total_amount"):
            self.total_entry.insert(0, f"{float(data['total_amount']):.2f}")
        self.total_entry.grid(row=0, column=10, padx=2, pady=3, sticky="ew")
        self.total_entry.bind("<KeyRelease>", lambda e: self.on_recalc())

        # 11. Delete Button
        del_btn = ctk.CTkButton(
            self,
            text="✕",
            width=26,
            height=26,
            fg_color="transparent",
            text_color=Theme.DANGER,
            hover_color=("#FEE2E2", "#7F1D1D"),
            command=self.delete_self
        )
        del_btn.grid(row=0, column=11, padx=2, pady=3)

        # If coverage was not provided in data, look up from catalog
        if not data.get("coverage_area"):
            self.apply_catalog_specs(self.brand_combo.get().strip(), self.size_combo.get().strip())

    _brands_cache = None
    _brand_sizes_cache = {}

    @classmethod
    def invalidate_catalog_cache(cls):
        """Invalidates catalog caches when new brands or sizes are added."""
        cls._brands_cache = None
        cls._brand_sizes_cache.clear()

    @classmethod
    def get_active_brands_from_db(cls, force_refresh: bool = False) -> list[str]:
        """Fetches active brands directly from database with caching for high performance."""
        if not force_refresh and cls._brands_cache is not None:
            return list(cls._brands_cache)

        from app.database.models import TileBrand
        try:
            records = list(TileBrand.select().where(TileBrand.is_active == True).order_by(TileBrand.name))
            names = [b.name for b in records]
            if names:
                cls._brands_cache = names
                return list(names)
        except Exception:
            pass
        return [
            "Kajaria Eternity",
            "Simpolo Ceramics",
            "Somany Ceramics",
            "Qutone Ceramic",
            "Nexion Surfaces",
            "AMA Signature Collection",
        ]

    @classmethod
    def fetch_brand_sizes_from_db(cls, brand_name: str, force_refresh: bool = False) -> list[str]:
        """Fetches ONLY the exact sizes configured for this specific brand with caching."""
        b_clean = (brand_name or "").strip()
        if not b_clean:
            return []

        cache_key = b_clean.lower()
        if not force_refresh and cache_key in cls._brand_sizes_cache:
            return list(cls._brand_sizes_cache[cache_key])

        from peewee import fn
        from app.database.models import BrandSizeCoverage, TileBrand

        # 1. Exact case-insensitive match for brand
        records = (
            BrandSizeCoverage.select(BrandSizeCoverage.size)
            .join(TileBrand)
            .where(
                (fn.LOWER(TileBrand.name) == b_clean.lower()) &
                (TileBrand.is_active == True)
            )
            .order_by(BrandSizeCoverage.id)
        )
        sizes = [r.size.strip() for r in records if r.size.strip()]

        # 2. Fallback to partial match if exact didn't return
        if not sizes:
            records = (
                BrandSizeCoverage.select(BrandSizeCoverage.size)
                .join(TileBrand)
                .where(
                    (TileBrand.name.ilike(f"%{b_clean}%")) &
                    (TileBrand.is_active == True)
                )
                .order_by(BrandSizeCoverage.id)
            )
            sizes = [r.size.strip() for r in records if r.size.strip()]

        cls._brand_sizes_cache[cache_key] = sizes
        return list(sizes)

    def get_sizes_for_brand(self, brand_name: str, force_refresh: bool = False) -> list[str]:
        """Returns BRAND-WISE SIZES ONLY for the selected brand directly from database."""
        brand_sizes = self.fetch_brand_sizes_from_db(brand_name, force_refresh=force_refresh)
        b_label = brand_name.strip() if brand_name else "Brand"
        if brand_sizes:
            # STRICTLY BRAND-WISE SIZES ONLY + quick add shortcut
            return brand_sizes + [f"+ Add New Size for {b_label}..."]

        if brand_name and brand_name.strip():
            return [f"+ Add First Size for {b_label}..."]

        return ["Select a Brand First"]

    def _setup_dynamic_dropdown_auto_refresh(self):
        """Auto-refreshes brand and size options directly from SQLite on every dropdown open."""
        try:
            orig_open_brand = self.brand_combo._open_dropdown_menu
            def on_open_brand_dropdown():
                fresh_brands = self.get_active_brands_from_db(force_refresh=True)
                if fresh_brands:
                    self.brand_combo.configure(values=fresh_brands)
                orig_open_brand()
            self.brand_combo._open_dropdown_menu = on_open_brand_dropdown
        except Exception:
            pass

        try:
            orig_open_size = self.size_combo._open_dropdown_menu
            def on_open_size_dropdown():
                curr_brand = self.brand_combo.get().strip()
                fresh_sizes = self.get_sizes_for_brand(curr_brand, force_refresh=True)
                self.size_combo.configure(values=fresh_sizes)
                orig_open_size()
            self.size_combo._open_dropdown_menu = on_open_size_dropdown
        except Exception:
            pass

    def on_brand_selected(self, chosen_brand=None):
        """When brand changes, strictly update to that brand's sizes only."""
        b = (chosen_brand or self.brand_combo.get()).strip()
        if chosen_brand:
            self.brand_combo.set(b)
        sizes = self.get_sizes_for_brand(b)
        self.size_combo.configure(values=sizes)

        curr = self.size_combo.get().strip()
        genuine_sizes = [s for s in sizes if not s.startswith("+ Add")]

        # If current size doesn't belong to this newly selected brand, switch to first size of this brand
        if curr not in genuine_sizes:
            new_sz = genuine_sizes[0] if genuine_sizes else (sizes[0] if sizes else "")
            self.size_combo.set(new_sz)
            curr = new_sz

        self.apply_catalog_specs(b, curr)

    def on_size_selected(self, chosen_size=None):
        b = self.brand_combo.get().strip()
        s = (chosen_size or self.size_combo.get()).strip()
        if chosen_size:
            self.size_combo.set(s)
        if s.startswith("+ Add"):
            self.open_quick_add_size_modal(b)
            return
        self.apply_catalog_specs(b, s)


    def open_quick_add_size_modal(self, brand_name: str):
        """Quick dialog to add a new size to the selected brand on the fly."""
        b_name = (brand_name or "Brand").strip()
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Add New Size to {b_name}")
        dialog.geometry("450x420")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Add Size for '{b_name}'", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24)

        # Tile Size
        ctk.CTkLabel(f, text="Tile Size (e.g. 1200X1800 15MM):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        size_ent = ctk.CTkEntry(f, placeholder_text="e.g. 1200X1800 15MM")
        size_ent.pack(fill="x", pady=(2, 6))

        # Pieces per box
        ctk.CTkLabel(f, text="Pieces Per Box:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        pcs_ent = ctk.CTkEntry(f, placeholder_text="e.g. 2")
        pcs_ent.insert(0, "2")
        pcs_ent.pack(fill="x", pady=(2, 6))

        # Coverage Area in Sqft
        ctk.CTkLabel(f, text="Coverage Area in Sqft Per Box:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        cov_ent = ctk.CTkEntry(f, placeholder_text="e.g. 23.25")
        cov_ent.insert(0, "15.50")
        cov_ent.pack(fill="x", pady=(2, 6))

        # Default Rate per Sqft
        ctk.CTkLabel(f, text="Default Rate Per Sqft (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        rate_sqft_ent = ctk.CTkEntry(f, placeholder_text="e.g. 145.00")
        rate_sqft_ent.pack(fill="x", pady=(2, 6))

        # Default Box Price
        ctk.CTkLabel(f, text="Default Box Price (₹) (Auto-calculated):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        rate_box_ent = ctk.CTkEntry(f, placeholder_text="e.g. 3371.25")
        rate_box_ent.pack(fill="x", pady=(2, 12))

        def auto_calc_box(e=None):
            try:
                c = float(cov_ent.get().strip() or 0.0)
                r = float(rate_sqft_ent.get().strip() or 0.0)
                if c > 0 and r > 0:
                    bp = round(c * r, 2)
                    rate_box_ent.delete(0, "end")
                    rate_box_ent.insert(0, f"{bp:.2f}")
            except Exception:
                pass

        rate_sqft_ent.bind("<KeyRelease>", auto_calc_box)
        cov_ent.bind("<KeyRelease>", auto_calc_box)

        def save_quick_size():
            sz = size_ent.get().strip()
            if not sz:
                msgbox.showwarning("Notice", "Size name is required.", parent=dialog)
                return

            try:
                pcs = int(pcs_ent.get().strip() or 2)
                cov = float(cov_ent.get().strip() or 15.5)
                r_sqft = float(rate_sqft_ent.get().strip() or 0.0)
                r_box = float(rate_box_ent.get().strip() or 0.0)
                if r_box <= 0 and r_sqft > 0 and cov > 0:
                    r_box = round(r_sqft * cov, 2)
            except ValueError:
                msgbox.showerror("Error", "Please enter valid numeric numbers.", parent=dialog)
                return

            from app.database.models import TileBrand, BrandSizeCoverage
            # Find or create brand
            brand_obj = TileBrand.select().where(TileBrand.name.ilike(b_name)).first()
            if not brand_obj:
                brand_obj = TileBrand.create(name=b_name)

            # Save in BrandSizeCoverage
            existing = BrandSizeCoverage.select().where(
                (BrandSizeCoverage.brand == brand_obj) &
                (BrandSizeCoverage.size.ilike(sz))
            ).first()
            if existing:
                existing.coverage_sqft = cov
                existing.pieces_per_box = pcs
                existing.default_rate_sqft = r_sqft
                existing.default_rate_box = r_box
                existing.save()
            else:
                BrandSizeCoverage.create(
                    brand=brand_obj,
                    size=sz,
                    pieces_per_box=pcs,
                    coverage_sqft=cov,
                    default_rate_sqft=r_sqft,
                    default_rate_box=r_box
                )

            dialog.destroy()

            # Invalidate cache and refresh sizes for this row
            ItemRowWidget.invalidate_catalog_cache()
            fresh_sizes = self.get_sizes_for_brand(b_name, force_refresh=True)
            self.size_combo.configure(values=fresh_sizes)
            self.size_combo.set(sz)

            # Auto-fill coverage and prices in row
            self.cov_entry.delete(0, "end")
            self.cov_entry.insert(0, f"{cov:g}")
            if r_sqft > 0:
                self.rate_sqft_entry.delete(0, "end")
                self.rate_sqft_entry.insert(0, f"{r_sqft:.2f}")
            if r_box > 0:
                self.rate_box_entry.delete(0, "end")
                self.rate_box_entry.insert(0, f"{r_box:.2f}")

            self.recalculate_amount("cov")

        ctk.CTkButton(
            dialog,
            text=f"Save Size for {b_name}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=save_quick_size
        ).pack(pady=(0, 20))

    def apply_catalog_specs(self, brand: str, size: str):
        """Fetches exact packaging coverage and rates directly from database for the brand and size."""
        from peewee import fn
        from app.database.models import BrandSizeCoverage, TileBrand
        b_clean = (brand or "").strip()
        s_clean = (size or "").strip()
        if not b_clean or not s_clean or s_clean.startswith("+ Add") or s_clean.startswith("Select a"):
            return

        rec = (
            BrandSizeCoverage.select()
            .join(TileBrand)
            .where(
                (fn.LOWER(TileBrand.name) == b_clean.lower()) &
                (fn.LOWER(BrandSizeCoverage.size) == s_clean.lower())
            )
            .first()
        )
        if not rec:
            rec = (
                BrandSizeCoverage.select()
                .join(TileBrand)
                .where(
                    (TileBrand.name.ilike(f"%{b_clean}%")) &
                    (fn.LOWER(BrandSizeCoverage.size) == s_clean.lower())
                )
                .first()
            )

        if rec:
            cov = rec.coverage_sqft or 0.0
            if cov > 0:
                self.cov_entry.delete(0, "end")
                self.cov_entry.insert(0, f"{cov:g}")

            if not self.rate_sqft_entry.get().strip() and (rec.default_rate_sqft or 0.0) > 0:
                self.rate_sqft_entry.delete(0, "end")
                self.rate_sqft_entry.insert(0, f"{rec.default_rate_sqft:.2f}")

            if not self.rate_box_entry.get().strip() and (rec.default_rate_box or 0.0) > 0:
                self.rate_box_entry.delete(0, "end")
                self.rate_box_entry.insert(0, f"{rec.default_rate_box:.2f}")

            self.recalculate_amount("cov")

    def on_tax_mode_changed(self, chosen_val=None):
        self.recalculate_amount("tax_mode")

    def recalculate_amount(self, trigger_source="sqft"):
        """Auto calculates Sqft <-> Boxes and Rates using Coverage Area."""
        if self._is_updating:
            return
        self._is_updating = True
        try:
            sqft_txt = self.sqft_entry.get().strip()
            rate_sqft_txt = self.rate_sqft_entry.get().strip()
            box_txt = self.box_entry.get().strip()
            rate_box_txt = self.rate_box_entry.get().strip()
            cov_txt = self.cov_entry.get().strip()

            cov = float(cov_txt) if cov_txt else 0.0
            q_sqft = float(sqft_txt) if sqft_txt else 0.0
            r_sqft = float(rate_sqft_txt) if rate_sqft_txt else 0.0
            q_box = float(box_txt) if box_txt else 0.0
            r_box = float(rate_box_txt) if rate_box_txt else 0.0

            calc_amount = 0.0

            if trigger_source in ["sqft", "tax_mode"]:
                if cov > 0 and q_sqft > 0:
                    q_box = round(q_sqft / cov, 2)
                    self.box_entry.delete(0, "end")
                    self.box_entry.insert(0, f"{q_box:g}")
                if cov > 0 and r_sqft > 0 and (r_box == 0 or not rate_box_txt or trigger_source == "tax_mode"):
                    r_box = round(r_sqft * cov, 2)
                    self.rate_box_entry.delete(0, "end")
                    self.rate_box_entry.insert(0, f"{r_box:.2f}")
                if q_sqft > 0 and r_sqft > 0:
                    calc_amount = round(q_sqft * r_sqft, 2)
                elif q_box > 0 and r_box > 0:
                    calc_amount = round(q_box * r_box, 2)

            elif trigger_source == "box":
                if cov > 0 and q_box > 0:
                    q_sqft = round(q_box * cov, 2)
                    self.sqft_entry.delete(0, "end")
                    self.sqft_entry.insert(0, f"{q_sqft:g}")
                if cov > 0 and r_box > 0 and (r_sqft == 0 or not rate_sqft_txt):
                    r_sqft = round(r_box / cov, 2)
                    self.rate_sqft_entry.delete(0, "end")
                    self.rate_sqft_entry.insert(0, f"{r_sqft:.2f}")
                if q_box > 0 and r_box > 0:
                    calc_amount = round(q_box * r_box, 2)
                elif q_sqft > 0 and r_sqft > 0:
                    calc_amount = round(q_sqft * r_sqft, 2)

            elif trigger_source == "rate_sqft":
                if cov > 0 and r_sqft > 0:
                    r_box = round(r_sqft * cov, 2)
                    self.rate_box_entry.delete(0, "end")
                    self.rate_box_entry.insert(0, f"{r_box:.2f}")
                if q_sqft > 0 and r_sqft > 0:
                    calc_amount = round(q_sqft * r_sqft, 2)
                elif q_box > 0 and r_box > 0:
                    calc_amount = round(q_box * r_box, 2)

            elif trigger_source == "rate_box":
                if cov > 0 and r_box > 0:
                    r_sqft = round(r_box / cov, 2)
                    self.rate_sqft_entry.delete(0, "end")
                    self.rate_sqft_entry.insert(0, f"{r_sqft:.2f}")
                if q_box > 0 and r_box > 0:
                    calc_amount = round(q_box * r_box, 2)
                elif q_sqft > 0 and r_sqft > 0:
                    calc_amount = round(q_sqft * r_sqft, 2)

            elif trigger_source == "cov":
                if cov > 0:
                    if q_sqft > 0:
                        q_box = round(q_sqft / cov, 2)
                        self.box_entry.delete(0, "end")
                        self.box_entry.insert(0, f"{q_box:g}")
                    elif q_box > 0:
                        q_sqft = round(q_box * cov, 2)
                        self.sqft_entry.delete(0, "end")
                        self.sqft_entry.insert(0, f"{q_sqft:g}")

                    if r_sqft > 0:
                        r_box = round(r_sqft * cov, 2)
                        self.rate_box_entry.delete(0, "end")
                        self.rate_box_entry.insert(0, f"{r_box:.2f}")
                    elif r_box > 0:
                        r_sqft = round(r_box / cov, 2)
                        self.rate_sqft_entry.delete(0, "end")
                        self.rate_sqft_entry.insert(0, f"{r_sqft:.2f}")

                if q_sqft > 0 and r_sqft > 0:
                    calc_amount = round(q_sqft * r_sqft, 2)
                elif q_box > 0 and r_box > 0:
                    calc_amount = round(q_box * r_box, 2)

            if calc_amount > 0:
                self.total_entry.delete(0, "end")
                self.total_entry.insert(0, f"{calc_amount:.2f}")

        except Exception:
            pass
        finally:
            self._is_updating = False

        self.on_recalc()

    def apply_discount_factor(self, factor: float):
        """Applies a proportional discount factor directly to this item's unit rates and line total."""
        if self._is_updating:
            return
        self._is_updating = True
        try:
            cov_txt = self.cov_entry.get().strip()
            cov = float(cov_txt) if cov_txt else 0.0
            sqft_txt = self.sqft_entry.get().strip()
            sqft = float(sqft_txt) if sqft_txt else 0.0
            box_txt = self.box_entry.get().strip()
            boxes = float(box_txt) if box_txt else 0.0

            rate_sqft_txt = self.rate_sqft_entry.get().strip()
            rate_sqft = float(rate_sqft_txt) if rate_sqft_txt else 0.0

            rate_box_txt = self.rate_box_entry.get().strip()
            rate_box = float(rate_box_txt) if rate_box_txt else 0.0

            tot_txt = self.total_entry.get().strip()
            tot = float(tot_txt) if tot_txt else 0.0

            if tot <= 0:
                if sqft > 0 and rate_sqft > 0:
                    tot = sqft * rate_sqft
                elif boxes > 0 and rate_box > 0:
                    tot = boxes * rate_box

            if tot > 0:
                new_tot = round(tot * factor, 2)
                self.total_entry.delete(0, "end")
                self.total_entry.insert(0, f"{new_tot:.2f}")

                if sqft > 0:
                    new_r_sqft = round(new_tot / sqft, 2)
                    self.rate_sqft_entry.delete(0, "end")
                    self.rate_sqft_entry.insert(0, f"{new_r_sqft:.2f}")
                    if cov > 0:
                        new_r_box = round(new_r_sqft * cov, 2)
                        self.rate_box_entry.delete(0, "end")
                        self.rate_box_entry.insert(0, f"{new_r_box:.2f}")
                elif boxes > 0:
                    new_r_box = round(new_tot / boxes, 2)
                    self.rate_box_entry.delete(0, "end")
                    self.rate_box_entry.insert(0, f"{new_r_box:.2f}")
                    if cov > 0:
                        new_r_sqft = round(new_r_box / cov, 2)
                        self.rate_sqft_entry.delete(0, "end")
                        self.rate_sqft_entry.insert(0, f"{new_r_sqft:.2f}")
                elif rate_sqft > 0:
                    new_r_sqft = round(rate_sqft * factor, 2)
                    self.rate_sqft_entry.delete(0, "end")
                    self.rate_sqft_entry.insert(0, f"{new_r_sqft:.2f}")
                    if cov > 0:
                        new_r_box = round(new_r_sqft * cov, 2)
                        self.rate_box_entry.delete(0, "end")
                        self.rate_box_entry.insert(0, f"{new_r_box:.2f}")
        finally:
            self._is_updating = False

    def get_data(self):
        try:
            cov = float(self.cov_entry.get().strip() or 0.0)
        except ValueError:
            cov = 0.0
        try:
            sqft = float(self.sqft_entry.get().strip() or 0.0)
        except ValueError:
            sqft = 0.0
        try:
            r_sqft = float(self.rate_sqft_entry.get().strip() or 0.0)
        except ValueError:
            r_sqft = 0.0
        try:
            boxes = float(self.box_entry.get().strip() or 0.0)
        except ValueError:
            boxes = 0.0
        try:
            r_box = float(self.rate_box_entry.get().strip() or 0.0)
        except ValueError:
            r_box = 0.0
        try:
            tot = float(self.total_entry.get().strip() or 0.0)
        except ValueError:
            tot = round(sqft * r_sqft if sqft and r_sqft else boxes * r_box, 2)

        tax_str = self.tax_combo.get().strip() if hasattr(self, "tax_combo") else "Excl. 18%"
        tax_mode = "inclusive" if "Incl" in tax_str else "exclusive"

        if tot <= 0:
            if sqft > 0 and r_sqft > 0:
                tot = round(sqft * r_sqft, 2)
            elif boxes > 0 and r_box > 0:
                tot = round(boxes * r_box, 2)

        if tax_mode == "inclusive":
            line_gross = tot
            taxable_amt = round(line_gross / 1.18, 2)
            gst_amt = round(line_gross - taxable_amt, 2)
        else:
            taxable_amt = tot
            gst_amt = round(taxable_amt * 0.18, 2)
            line_gross = round(taxable_amt + gst_amt, 2)

        return {
            "sl_no": self.sl_no,
            "description": self.desc_entry.get().strip(),
            "size": self.size_combo.get().strip(),
            "brand": self.brand_combo.get().strip(),
            "coverage_area": cov,
            "quantity_sqft": sqft,
            "rate_per_sqft": r_sqft,
            "tax_mode": tax_mode,
            "tax_percent": 18.0,
            "taxable_amount": taxable_amt,
            "gst_amount": gst_amt,
            "line_gross": line_gross,
            "quantity_boxes": boxes,
            "rate_per_box": r_box,
            "total_amount": tot,
        }

    def delete_self(self):
        if self.on_delete:
            self.on_delete(self)


class AreaSectionWidget(ctk.CTkFrame):
    """Section container grouping items under a project area (e.g. Kids Bathroom, Ground Floor)."""
    def __init__(self, master, area_name: str, on_recalc, on_remove_area=None, area_data=None, catalog_context=None, **kwargs):
        default_tax_mode = kwargs.pop("default_tax_mode", "exclusive")
        super().__init__(
            master,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER,
            **kwargs
        )
        self.default_tax_mode = default_tax_mode
        self.on_recalc = on_recalc
        self.on_remove_area = on_remove_area
        self.catalog_context = catalog_context or {}
        self.item_widgets = []

        # 1. Area Section Header
        self.header = ctk.CTkFrame(self, fg_color=("#0F172A", "#0B0F19"), corner_radius=12, height=36)
        self.header.pack(fill="x", padx=6, pady=6)

        icon_lbl = ctk.CTkLabel(
            self.header,
            text="✦ AREA:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=Theme.ACCENT_GOLD
        )
        icon_lbl.pack(side="left", padx=(10, 4))

        self.name_entry = ctk.CTkEntry(
            self.header,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            width=260,
            height=28,
            corner_radius=Theme.RADIUS_SM,
            fg_color=("#1E293B", "#1F2937"),
            text_color="white",
            border_color="#475569"
        )
        self.name_entry.insert(0, area_name)
        self.name_entry.pack(side="left", padx=4)

        del_area_btn = ctk.CTkButton(
            self.header,
            text="Remove Area 🗑️",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
            width=95,
            height=26,
            corner_radius=Theme.RADIUS_SM,
            fg_color="transparent",
            text_color=Theme.DANGER,
            border_width=1,
            border_color=Theme.BTN_DANGER_BORDER,
            hover_color=("#7F1D1D", "#450A0A"),
            command=self.remove_self
        )
        del_area_btn.pack(side="right", padx=10)

        # 2. Table Column Titles (12 columns matching layout + Action button)
        col_bar = ctk.CTkFrame(self, fg_color=(Theme.STONE, "#242220"), height=30, corner_radius=Theme.RADIUS_SM)
        col_bar.pack(fill="x", padx=8, pady=(2, 4))
        item_col_weights = [1, 5, 2, 3, 2, 2, 2, 2, 2, 2, 2, 1]
        for idx, w in enumerate(item_col_weights):
            col_bar.grid_columnconfigure(idx, weight=w, uniform="area_item_cols")

        cols = [
            "Sl.",
            "Item Description",
            "Size",
            "Brand",
            "Cov (Sqft/Bx)",
            "Qty Sqft",
            "₹ / Sqft",
            "Tax (18%)",
            "Boxes",
            "₹ / Box",
            "Total (₹)",
            ""
        ]
        for i, c in enumerate(cols):
            ctk.CTkLabel(
                col_bar,
                text=c,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER)
            ).grid(row=0, column=i, padx=2, pady=2, sticky="ew")

        # 3. Items Container Frame
        self.items_container = ctk.CTkFrame(self, fg_color="transparent")
        self.items_container.pack(fill="x", padx=8, pady=(0, 6))

        # 4. Bottom Controls: "+ Add Item" & Area Subtotal
        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=10, pady=(2, 8))

        add_item_btn = ctk.CTkButton(
            bot_bar,
            text="+ Add Tile Item",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            width=120,
            height=30,
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.add_item
        )
        add_item_btn.pack(side="left")

        self.area_subtotal_lbl = ctk.CTkLabel(
            bot_bar,
            text="Area Total (with Tax): ₹ 0.00",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=Theme.PRIMARY
        )
        self.area_subtotal_lbl.pack(side="right")

        # Populate initial or passed items
        if area_data and area_data.get("items"):
            for it in area_data["items"]:
                self.add_item(data=it)
        else:
            self.add_item()

    def add_item(self, data=None):
        sl = len(self.item_widgets) + 1
        if data is None:
            data = {"tax_mode": getattr(self, "default_tax_mode", "exclusive")}
        item_row = ItemRowWidget(
            self.items_container,
            on_recalc=self.on_item_recalc,
            sl_no=sl,
            data=data,
            on_delete=self.delete_item,
            catalog_context=self.catalog_context
        )
        item_row.pack(fill="x", pady=2)
        self.item_widgets.append(item_row)
        self.on_item_recalc()

    def delete_item(self, item_widget):
        if len(self.item_widgets) <= 1:
            msgbox.showwarning("Notice", "An area section must have at least one item row.")
            return
        if item_widget in self.item_widgets:
            self.item_widgets.remove(item_widget)
            item_widget.destroy()
            # Renumber
            for idx, w in enumerate(self.item_widgets, start=1):
                w.sl_no = idx
                w.sl_label.configure(text=str(idx))
            self.on_item_recalc()

    def on_item_recalc(self):
        subtotal = 0.0
        for w in self.item_widgets:
            d = w.get_data()
            has_content = (
                bool(d["description"].strip()) or
                d["quantity_sqft"] > 0 or
                d["quantity_boxes"] > 0 or
                d["rate_per_sqft"] > 0 or
                d["rate_per_box"] > 0 or
                d["total_amount"] > 0
            )
            if has_content:
                subtotal += d.get("line_gross", 0.0)
        self.area_subtotal_lbl.configure(text=f"Area Total (with Tax): ₹ {subtotal:,.2f}")
        self.on_recalc()

    def remove_self(self):
        if self.on_remove_area:
            self.on_remove_area(self)

    def get_data(self):
        items = []
        for w in self.item_widgets:
            d = w.get_data()
            has_content = (
                bool(d["description"].strip()) or
                d["quantity_sqft"] > 0 or
                d["quantity_boxes"] > 0 or
                d["rate_per_sqft"] > 0 or
                d["rate_per_box"] > 0 or
                d["total_amount"] > 0
            )
            if has_content:
                if not d["description"].strip():
                    brand = d.get("brand", "").strip()
                    size = d.get("size", "").strip()
                    if brand or size:
                        d["description"] = f"{brand} {size} Tile".strip()
                    else:
                        d["description"] = f"Tile Item #{d.get('sl_no', 1)}"
                items.append(d)
        return {
            "area_name": self.name_entry.get().strip() or "General Area",
            "items": items,
        }



class QuotationEditorView(ctk.CTkFrame):
    def __init__(self, master, controller, quote_id=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.quote_id = quote_id
        self.area_widgets = []
        self.customers_cache = []
        self.salespersons_cache = []
        self.catalog_context = {}
        self.matched_customer_id = None
        self._current_cust_matches = []

        self.build_ui()
        self.load_data()

    def build_ui(self):
        # 1. Top Bar with Title & Action Buttons
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 12))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        self.title_lbl = ctk.CTkLabel(
            title_box,
            text="Quotation Builder",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER),
        )
        self.title_lbl.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Configure customer details, area groupings, sqft/box rates & live totals",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=("#615D56", "#A8A297"),
        )
        subtitle.pack(anchor="w")

        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right")

        back_btn = ctk.CTkButton(
            btn_box,
            text="← Back to List",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            hover_color=Theme.PRIMARY,
            command=lambda: self.controller.show_view("quotations", None),
            height=36
        )
        back_btn.pack(side="left", padx=4)

        brand_cat_btn = ctk.CTkButton(
            btn_box,
            text="🏷️ Brands & Coverage",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            hover_color=Theme.PRIMARY,
            command=lambda: self.controller.show_view("brand_catalog"),
            height=36
        )
        brand_cat_btn.pack(side="left", padx=4)

        sync_cat_btn = ctk.CTkButton(
            btn_box,
            text="🔄 Sync Catalog",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            hover_color=Theme.PRIMARY,
            command=self.refresh_catalog_data,
            height=36
        )
        sync_cat_btn.pack(side="left", padx=4)

        save_pdf_btn = ctk.CTkButton(
            btn_box,
            text="📄 Save & Export PDF",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            hover_color=Theme.SUCCESS_HOVER,
            command=self.save_and_export_pdf,
            height=36
        )
        save_pdf_btn.pack(side="left", padx=4)

        save_btn = ctk.CTkButton(
            btn_box,
            text="💾 Save Quotation",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            corner_radius=Theme.RADIUS_PILL,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.save_quotation,
            height=36
        )
        save_btn.pack(side="left", padx=4)

        # Scrollable container for full quotation document
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 2. Header Card (Customer, Quotation No, Date, Sales Rep)
        header_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        header_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            header_card,
            text="📋 Quotation Header & Client Information",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(anchor="w", padx=16, pady=(12, 8))

        form_grid = ctk.CTkFrame(header_card, fg_color="transparent")
        form_grid.pack(fill="x", padx=16, pady=(0, 14))
        form_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Quotation Number
        ctk.CTkLabel(form_grid, text="Quotation Number:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=6, pady=(4, 2), sticky="w")
        self.quote_num_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11, weight="bold"))
        self.quote_num_entry.grid(row=1, column=0, padx=6, pady=(0, 8), sticky="ew")

        # Date
        ctk.CTkLabel(form_grid, text="Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=6, pady=(4, 2), sticky="w")
        self.date_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11))
        self.date_entry.insert(0, str(date.today()))
        self.date_entry.grid(row=1, column=1, padx=6, pady=(0, 8), sticky="ew")

        # Customer Selector + Quick Add + Clear
        cust_label_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        cust_label_box.grid(row=0, column=2, padx=6, pady=(4, 2), sticky="ew")
        ctk.CTkLabel(cust_label_box, text="Customer:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")

        quick_cust_btn = ctk.CTkButton(
            cust_label_box,
            text="+ New Client",
            font=ctk.CTkFont(size=9, weight="bold"),
            width=68,
            height=18,
            fg_color="transparent",
            text_color=Theme.PRIMARY,
            command=self.open_quick_customer_modal
        )
        quick_cust_btn.pack(side="right")

        clear_cust_btn = ctk.CTkButton(
            cust_label_box,
            text="Clear",
            font=ctk.CTkFont(size=9),
            width=38,
            height=18,
            fg_color="transparent",
            text_color=("#615D56", "#A8A297"),
            hover_color=("#E5E7EB", "#374151"),
            command=self.clear_customer_fields
        )
        clear_cust_btn.pack(side="right", padx=(0, 4))

        self.customer_combo = ctk.CTkComboBox(form_grid, values=["Loading..."], font=ctk.CTkFont(size=11), command=self.on_customer_selected)
        self.customer_combo.grid(row=1, column=2, padx=6, pady=(0, 8), sticky="ew")
        if hasattr(self.customer_combo, "_entry"):
            self.customer_combo._entry.bind("<KeyRelease>", self._on_customer_key_release)

        # Sales Person Selector
        ctk.CTkLabel(form_grid, text="Lead Sales Associate:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, padx=6, pady=(4, 2), sticky="w")
        self.salesperson_combo = ctk.CTkComboBox(form_grid, values=["Loading..."], font=ctk.CTkFont(size=11), command=self._on_primary_salesperson_changed)
        self.salesperson_combo.grid(row=1, column=3, padx=6, pady=(0, 8), sticky="ew")

        # Auto-popup suggestions panel for matched existing customers from database
        self.cust_suggestions_card = ctk.CTkFrame(
            form_grid,
            fg_color=("#FFF7ED", "#221A16"),
            border_width=2,
            border_color=Theme.PRIMARY,
            corner_radius=10
        )
        # Not placed on grid initially; shown dynamically when search matches exist

        # Row 3: Contact, Project Name, Delivery Address
        ctk.CTkLabel(form_grid, text="Contact Phone:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=0, padx=6, pady=(4, 2), sticky="w")
        self.phone_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11), placeholder_text="e.g. 98240 77889")
        self.phone_entry.grid(row=4, column=0, padx=6, pady=(0, 4), sticky="ew")
        self.phone_entry.bind("<KeyRelease>", self._on_phone_key_release)
        self.phone_entry.bind("<Return>", self._on_phone_return)

        ctk.CTkLabel(form_grid, text="Project / Site Name:", font=ctk.CTkFont(size=11)).grid(row=3, column=1, padx=6, pady=(4, 2), sticky="w")
        self.project_name_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11), placeholder_text="e.g. 4-BHK Villa / Bungalow")
        self.project_name_entry.grid(row=4, column=1, padx=6, pady=(0, 4), sticky="ew")

        ctk.CTkLabel(form_grid, text="Site / Delivery Address:", font=ctk.CTkFont(size=11)).grid(row=3, column=2, columnspan=2, padx=6, pady=(4, 2), sticky="w")
        self.address_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11), placeholder_text="Full delivery address for logistics")
        self.address_entry.grid(row=4, column=2, columnspan=2, padx=6, pady=(0, 4), sticky="ew")

        # Row 5: Live Customer Database Status Badge
        self.cust_status_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        self.cust_status_frame.grid(row=5, column=0, columnspan=4, padx=6, pady=(2, 6), sticky="ew")

        self.cust_status_lbl = ctk.CTkLabel(
            self.cust_status_frame,
            text="ℹ Enter mobile number or customer name to search database records",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color=("#615D56", "#A8A297"),
            anchor="w"
        )
        self.cust_status_lbl.pack(side="left")

        # Row 6: Default Tax Setting for Sqft Rates
        tax_mode_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        tax_mode_frame.grid(row=6, column=0, columnspan=4, padx=6, pady=(6, 4), sticky="ew")

        ctk.CTkLabel(
            tax_mode_frame,
            text="Tax Option for Sqft Rate:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(0, 8))

        self.global_tax_combo = ctk.CTkOptionMenu(
            tax_mode_frame,
            values=["Excl. 18% Tax (+18% GST added)", "Incl. 18% Tax (18% GST included)"],
            font=ctk.CTkFont(size=11, weight="bold"),
            width=260,
            command=self.on_global_tax_changed
        )
        self.global_tax_combo.set("Excl. 18% Tax (+18% GST added)")
        self.global_tax_combo.pack(side="left", padx=(0, 10))

        apply_all_btn = ctk.CTkButton(
            tax_mode_frame,
            text="Apply to All Items ⟳",
            font=ctk.CTkFont(size=10, weight="bold"),
            width=135,
            height=28,
            corner_radius=Theme.RADIUS_BUTTON,
            border_width=Theme.BORDER_WIDTH_BUTTON,
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.PRIMARY,
            command=self.apply_global_tax_to_all_items
        )
        apply_all_btn.pack(side="left")

        # Row 7: Sales Collaboration & Commission Split (Assisted Salesperson)
        self.split_card = ctk.CTkFrame(
            form_grid,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#F8FAFC", "#1C1A18"),
            border_width=1,
            border_color=Theme.LIGHT_BORDER
        )
        self.split_card.grid(row=7, column=0, columnspan=4, padx=6, pady=(10, 4), sticky="ew")

        split_top_row = ctk.CTkFrame(self.split_card, fg_color="transparent")
        split_top_row.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            split_top_row,
            text="🤝 Sales Collaboration & Commission Split (Optional - Deals Closed by 2 Salespersons)",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left")

        # Controls Row
        split_ctrl_row = ctk.CTkFrame(self.split_card, fg_color="transparent")
        split_ctrl_row.pack(fill="x", padx=12, pady=(0, 6))

        # Assisted Salesperson Dropdown
        ctk.CTkLabel(split_ctrl_row, text="Assisted By:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.assisted_combo = ctk.CTkComboBox(
            split_ctrl_row,
            values=["None (Solo Sale)"],
            font=ctk.CTkFont(size=11),
            width=210,
            command=self._on_assisted_salesperson_changed
        )
        self.assisted_combo.set("None (Solo Sale)")
        self.assisted_combo.pack(side="left", padx=(0, 12))

        # Split Mode Option
        ctk.CTkLabel(split_ctrl_row, text="Split Share By:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.split_mode_combo = ctk.CTkOptionMenu(
            split_ctrl_row,
            values=["Percentage (%)", "Amount (₹)"],
            font=ctk.CTkFont(size=10, weight="bold"),
            width=130,
            command=self._on_split_mode_changed
        )
        self.split_mode_combo.set("Percentage (%)")
        self.split_mode_combo.pack(side="left", padx=(0, 12))

        # Assisted Share % Entry
        ctk.CTkLabel(split_ctrl_row, text="Assisted (%):", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.assisted_share_pct_entry = ctk.CTkEntry(split_ctrl_row, width=70, font=ctk.CTkFont(size=11), placeholder_text="50.0")
        self.assisted_share_pct_entry.pack(side="left", padx=(0, 12))
        self.assisted_share_pct_entry.bind("<KeyRelease>", self._on_assisted_pct_key)

        # Assisted Share Amount Entry
        ctk.CTkLabel(split_ctrl_row, text="Assisted (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.assisted_share_amt_entry = ctk.CTkEntry(split_ctrl_row, width=105, font=ctk.CTkFont(size=11), placeholder_text="0.00")
        self.assisted_share_amt_entry.pack(side="left", padx=(0, 10))
        self.assisted_share_amt_entry.bind("<KeyRelease>", self._on_assisted_amt_key)

        # 50/50 Equal Split Quick Button
        self.equal_split_btn = ctk.CTkButton(
            split_ctrl_row,
            text="50/50 Split ⚖️",
            font=ctk.CTkFont(size=10, weight="bold"),
            width=90,
            height=28,
            corner_radius=Theme.RADIUS_PILL,
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.PRIMARY,
            command=self.set_equal_split
        )
        self.equal_split_btn.pack(side="left")

        # Live Split Preview Badge
        self.split_preview_lbl = ctk.CTkLabel(
            self.split_card,
            text="ℹ Solo Sale: 100% of quotation value is attributed to the lead sales associate.",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
            text_color=("#615D56", "#A8A297"),
            anchor="w"
        )
        self.split_preview_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # 3. Area Sections Bar
        area_control_card = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        area_control_card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            area_control_card,
            text="🏷️ Project Areas & Tile Specifications",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).pack(side="left")

        # Quick Area Buttons
        quick_areas_frame = ctk.CTkFrame(area_control_card, fg_color="transparent")
        quick_areas_frame.pack(side="right")

        ctk.CTkLabel(
            quick_areas_frame,
            text="Quick Add Area:",
            font=ctk.CTkFont(size=11),
            text_color=("#615D56", "#A8A297")
        ).pack(side="left", padx=4)

        for a_suggest in ["Kids Bathroom", "Ground Floor", "Master Bathroom", "Balcony", "Bar Counter"]:
            btn = ctk.CTkButton(
                quick_areas_frame,
                text=f"+ {a_suggest}",
                font=ctk.CTkFont(size=10, weight="bold"),
                height=26,
                corner_radius=Theme.RADIUS_SM,
                border_width=Theme.BORDER_WIDTH_BUTTON,
                fg_color=Theme.BTN_SECONDARY_BG,
                text_color=(Theme.BLACK, Theme.PAPER),
                hover_color=Theme.PRIMARY,
                command=lambda name=a_suggest: self.add_area(name)
            )
            btn.pack(side="left", padx=2)

        # 4. Container for Area Widgets
        self.areas_container = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        self.areas_container.pack(fill="x", pady=(0, 10))

        # Add custom area button
        add_custom_area_btn = ctk.CTkButton(
            self.scroll_body,
            text="+ Add Another Custom Area Section",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.INSET_BG,
            text_color=Theme.PRIMARY,
            hover_color=Theme.BTN_SECONDARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.PRIMARY,
            command=lambda: self.add_area("New Project Area"),
            height=36
        )
        add_custom_area_btn.pack(fill="x", pady=(0, 14))

        # 5. Bottom Financial Summary & Status Card
        totals_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=Theme.BORDER_WIDTH_CARD,
            border_color=Theme.LIGHT_BORDER
        )
        totals_card.pack(fill="x", pady=(0, 10))

        t_layout = ctk.CTkFrame(totals_card, fg_color="transparent")
        t_layout.pack(fill="x", padx=16, pady=16)
        t_layout.grid_columnconfigure(0, weight=3)
        t_layout.grid_columnconfigure(1, weight=2)

        # Left: Notes and Quotation Status
        left_notes = ctk.CTkFrame(t_layout, fg_color="transparent")
        left_notes.grid(row=0, column=0, padx=(0, 16), sticky="nsew")

        ctk.CTkLabel(
            left_notes,
            text="Quotation Status:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        self.status_combo = ctk.CTkComboBox(
            left_notes,
            values=["Open", "In-Review", "Won", "Lost"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=Theme.RADIUS_BUTTON,
            width=200
        )
        self.status_combo.set("Open")
        self.status_combo.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            left_notes,
            text="Special Notes / Customer Remarks:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        self.notes_entry = ctk.CTkTextbox(left_notes, height=75, font=ctk.CTkFont(size=11), corner_radius=Theme.RADIUS_INPUT, border_width=Theme.BORDER_WIDTH_INPUT, border_color=Theme.INSET_BORDER, fg_color=Theme.INSET_BG)
        self.notes_entry.pack(fill="x")

        # 3. Lump-Sum Discount & Item Price Distribution Tool
        disc_card = ctk.CTkFrame(
            left_notes,
            fg_color=("#FFF7ED", "#221A16"),
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.PRIMARY
        )
        disc_card.pack(fill="x", pady=(12, 0))

        disc_header = ctk.CTkFrame(disc_card, fg_color="transparent")
        disc_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            disc_header,
            text="🏷️ Lump-Sum Discount & Item Rate Distribution",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            disc_card,
            text="Distribute discount percentage directly across all item rates (no discount row shown in totals/PDF):",
            font=ctk.CTkFont(size=10),
            text_color=("#615D56", "#A8A297"),
            wraplength=420,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # Inputs Grid
        disc_grid = ctk.CTkFrame(disc_card, fg_color="transparent")
        disc_grid.pack(fill="x", padx=12, pady=(0, 6))
        disc_grid.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(disc_grid, text="Target Total (₹):", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=0, padx=4, sticky="w")
        self.discount_target_entry = ctk.CTkEntry(disc_grid, placeholder_text="e.g. 80000", height=28, font=ctk.CTkFont(size=11))
        self.discount_target_entry.grid(row=1, column=0, padx=4, pady=(2, 4), sticky="ew")
        self.discount_target_entry.bind("<KeyRelease>", self._on_discount_target_key)

        ctk.CTkLabel(disc_grid, text="OR Discount (₹):", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=1, padx=4, sticky="w")
        self.discount_val_entry = ctk.CTkEntry(disc_grid, placeholder_text="e.g. 5000", height=28, font=ctk.CTkFont(size=11))
        self.discount_val_entry.grid(row=1, column=1, padx=4, pady=(2, 4), sticky="ew")
        self.discount_val_entry.bind("<KeyRelease>", self._on_discount_val_key)

        ctk.CTkLabel(disc_grid, text="OR Discount (%):", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=2, padx=4, sticky="w")
        self.discount_pct_entry = ctk.CTkEntry(disc_grid, placeholder_text="e.g. 5.88", height=28, font=ctk.CTkFont(size=11))
        self.discount_pct_entry.grid(row=1, column=2, padx=4, pady=(2, 4), sticky="ew")
        self.discount_pct_entry.bind("<KeyRelease>", self._on_discount_pct_key)

        # Buttons Row
        disc_btn_row = ctk.CTkFrame(disc_card, fg_color="transparent")
        disc_btn_row.pack(fill="x", padx=12, pady=(0, 6))

        apply_disc_btn = ctk.CTkButton(
            disc_btn_row,
            text="Apply Discount to All Items ⚡",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.RADIUS_PILL,
            height=28,
            command=self.apply_distributed_discount
        )
        apply_disc_btn.pack(side="left", padx=(0, 6))

        clear_disc_btn = ctk.CTkButton(
            disc_btn_row,
            text="Reset",
            font=ctk.CTkFont(size=10),
            width=50,
            height=28,
            corner_radius=Theme.RADIUS_PILL,
            fg_color=Theme.BTN_SECONDARY_BG,
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.STONE,
            command=self.clear_discount_inputs
        )
        clear_disc_btn.pack(side="left")

        # Feedback Label
        self.discount_feedback_lbl = ctk.CTkLabel(
            disc_card,
            text="",
            font=ctk.CTkFont(size=10),
            wraplength=420,
            justify="left"
        )
        self.discount_feedback_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # Right: Financial Totals Box
        right_box = ctk.CTkFrame(t_layout, fg_color=Theme.INSET_BG, corner_radius=16, border_width=Theme.BORDER_WIDTH_CARD, border_color=Theme.INSET_BORDER)
        right_box.grid(row=0, column=1, sticky="nsew")

        r_grid = ctk.CTkFrame(right_box, fg_color="transparent")
        r_grid.pack(fill="both", expand=True, padx=14, pady=12)
        r_grid.grid_columnconfigure(0, weight=1)
        r_grid.grid_columnconfigure(1, weight=1)

        # 0. Taxable Subtotal
        ctk.CTkLabel(r_grid, text="Taxable Subtotal:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, pady=2, sticky="w")
        self.taxable_subtotal_lbl = ctk.CTkLabel(r_grid, text="₹ 0.00", font=ctk.CTkFont(size=11, weight="bold"))
        self.taxable_subtotal_lbl.grid(row=0, column=1, pady=2, sticky="e")

        # 1. CGST (9.0%)
        ctk.CTkLabel(r_grid, text="CGST (9.0%):", font=ctk.CTkFont(size=11)).grid(row=1, column=0, pady=2, sticky="w")
        self.cgst_lbl = ctk.CTkLabel(r_grid, text="₹ 0.00", font=ctk.CTkFont(size=11))
        self.cgst_lbl.grid(row=1, column=1, pady=2, sticky="e")

        # 2. SGST (9.0%)
        ctk.CTkLabel(r_grid, text="SGST (9.0%):", font=ctk.CTkFont(size=11)).grid(row=2, column=0, pady=2, sticky="w")
        self.sgst_lbl = ctk.CTkLabel(r_grid, text="₹ 0.00", font=ctk.CTkFont(size=11))
        self.sgst_lbl.grid(row=2, column=1, pady=2, sticky="e")

        # 3. Total 18% GST
        ctk.CTkLabel(r_grid, text="Total GST (18.0%):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.PRIMARY).grid(row=3, column=0, pady=2, sticky="w")
        self.total_gst_lbl = ctk.CTkLabel(r_grid, text="₹ 0.00", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.PRIMARY)
        self.total_gst_lbl.grid(row=3, column=1, pady=2, sticky="e")

        # 4. Gross Total (with Tax)
        ctk.CTkLabel(r_grid, text="Gross Total (with Tax):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=4, column=0, pady=(4, 2), sticky="w")
        self.gross_total_lbl = ctk.CTkLabel(r_grid, text="₹ 0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.gross_total_lbl.grid(row=4, column=1, pady=(4, 2), sticky="e")

        # 5. Round Off
        ctk.CTkLabel(r_grid, text="Round Off (±₹):", font=ctk.CTkFont(size=11)).grid(row=5, column=0, pady=2, sticky="w")
        self.round_off_entry = ctk.CTkEntry(r_grid, width=100, font=ctk.CTkFont(size=11))
        self.round_off_entry.insert(0, "0.00")
        self.round_off_entry.grid(row=5, column=1, pady=2, sticky="e")
        self.round_off_entry.bind("<KeyRelease>", lambda e: self.recalculate_totals())

        # 6. Net Total
        ctk.CTkLabel(
            r_grid,
            text="NET PAYABLE TOTAL:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).grid(row=6, column=0, pady=(8, 4), sticky="w")

        self.net_total_lbl = ctk.CTkLabel(
            r_grid,
            text="₹ 0.00",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=Theme.ACCENT_GOLD
        )
        self.net_total_lbl.grid(row=6, column=1, pady=(8, 4), sticky="e")

    def load_catalog_cache(self):
        try:
            self.brand_records = list(TileBrand.select().where(TileBrand.is_active == True).order_by(TileBrand.name))
            brand_names = [b.name for b in self.brand_records]
        except Exception:
            brand_names = []

        if not brand_names:
            brand_names = [
                "KAJARIA",
                "AGL",
                "Kajaria Eternity",
                "Simpolo Ceramics",
                "Somany",
                "Qutone",
                "Nexion",
                "AMA Signature Collection",
            ]

        brand_size_map = {}
        all_db_sizes = []
        size_to_spec = {}
        try:
            for r in BrandSizeCoverage.select(BrandSizeCoverage, TileBrand).join(TileBrand):
                bname = r.brand.name.strip() if r.brand else ""
                sname = r.size.strip()
                if not sname:
                    continue
                spec = {
                    "coverage_sqft": r.coverage_sqft,
                    "pieces_per_box": r.pieces_per_box,
                    "default_rate_sqft": r.default_rate_sqft,
                    "default_rate_box": r.default_rate_box,
                    "size": sname,
                    "brand": bname,
                }
                brand_size_map[(bname.lower(), sname.lower())] = spec
                if sname not in all_db_sizes:
                    all_db_sizes.append(sname)
                if sname.lower() not in size_to_spec:
                    size_to_spec[sname.lower()] = spec
        except Exception:
            pass

        all_unique_sizes = all_db_sizes + [s for s in COMMON_TILE_SIZES if s not in all_db_sizes]

        self.catalog_context.clear()
        self.catalog_context.update({
            "brand_names": brand_names,
            "brand_size_map": brand_size_map,
            "all_db_sizes": all_db_sizes,
            "all_sizes": all_unique_sizes,
            "size_to_spec": size_to_spec,
        })

    def refresh_catalog_data(self):
        """Refreshes catalog cache from DB and updates all active row dropdowns without losing quote entries."""
        self.load_catalog_cache()
        brand_names = self.catalog_context.get("brand_names", [])
        for aw in self.area_widgets:
            for iw in aw.item_widgets:
                curr_b = iw.brand_combo.get().strip()
                sizes = iw.get_sizes_for_brand(curr_b)
                iw.brand_combo.configure(values=brand_names)
                iw.size_combo.configure(values=sizes)
        msgbox.showinfo("Catalog Synced", f"Catalog synced successfully!\nLoaded {len(self.catalog_context.get('all_db_sizes', []))} sizes across {len(brand_names)} active brands.")


    def load_data(self):
        # 0. Load Tile Brand & Size Coverage Catalog
        self.load_catalog_cache()

        # 1. Load Customers & Sales Persons
        self.customers_cache = list(Customer.select().order_by(Customer.name))
        cust_names = [f"{c.name} ({c.mobile_number})" for c in self.customers_cache]
        if cust_names:
            self.customer_combo.configure(values=cust_names)
            if not self.quote_id:
                self.customer_combo.set(cust_names[0])
                self.apply_customer(self.customers_cache[0])

        self.salespersons_cache = list(SalesPerson.select().where(SalesPerson.is_active == True))
        sp_names = [f"{s.name} ({s.role})" for s in self.salespersons_cache]
        if sp_names:
            self.salesperson_combo.configure(values=sp_names)
            # Default to active user if salesperson
            active_u = self.controller.get_active_user()
            if active_u:
                for idx, s in enumerate(self.salespersons_cache):
                    if s.id == active_u.id:
                        self.salesperson_combo.set(sp_names[idx])
                        break
            else:
                self.salesperson_combo.set(sp_names[0])

        if hasattr(self, "assisted_combo"):
            assisted_vals = ["None (Solo Sale)"] + sp_names
            self.assisted_combo.configure(values=assisted_vals)
            self.assisted_combo.set("None (Solo Sale)")

        # 2. Check if editing existing quote or new quote
        if self.quote_id:
            quote_data = QuotationService.get_quotation_details(self.quote_id)
            if quote_data:
                self.title_lbl.configure(text=f"Editing Quotation: {quote_data['quotation_number']}")
                self.quote_num_entry.delete(0, "end")
                self.quote_num_entry.insert(0, quote_data["quotation_number"])

                q_d = quote_data["quotation_date"]
                self.date_entry.delete(0, "end")
                self.date_entry.insert(0, str(q_d))

                # Select customer
                for idx, c in enumerate(self.customers_cache):
                    if c.id == quote_data["customer_id"]:
                        self.customer_combo.set(cust_names[idx])
                        self.matched_customer_id = c.id
                        self.update_customer_status(f"✓ Existing Customer: {c.name} — Loaded from database", status_type="success")
                        break

                # Select primary salesperson
                for idx, s in enumerate(self.salespersons_cache):
                    if s.id == quote_data["sales_person_id"]:
                        self.salesperson_combo.set(sp_names[idx])
                        break

                # Select assisted salesperson if present
                asst_id = quote_data.get("assisted_by_id")
                if asst_id and hasattr(self, "assisted_combo"):
                    for idx, s in enumerate(self.salespersons_cache):
                        if s.id == asst_id:
                            self.assisted_combo.set(sp_names[idx])
                            break
                    split_t = quote_data.get("split_type", "percentage")
                    if split_t == "amount":
                        self.split_mode_combo.set("Amount (₹)")
                    else:
                        self.split_mode_combo.set("Percentage (%)")

                    share_val = float(quote_data.get("assisted_share_value", 50.0) or 50.0)
                    if split_t == "amount":
                        self.assisted_share_amt_entry.delete(0, "end")
                        self.assisted_share_amt_entry.insert(0, f"{share_val:.2f}")
                    else:
                        self.assisted_share_pct_entry.delete(0, "end")
                        self.assisted_share_pct_entry.insert(0, f"{share_val:.1f}")
                else:
                    if hasattr(self, "assisted_combo"):
                        self.assisted_combo.set("None (Solo Sale)")
                        self.assisted_share_pct_entry.delete(0, "end")
                        self.assisted_share_amt_entry.delete(0, "end")

                self.phone_entry.delete(0, "end")
                self.phone_entry.insert(0, quote_data["customer_phone"])

                self.address_entry.delete(0, "end")
                self.address_entry.insert(0, quote_data["delivery_address"])

                self.project_name_entry.delete(0, "end")
                self.project_name_entry.insert(0, quote_data["project_name"] or "")

                self.status_combo.set(quote_data["status"])

                self.notes_entry.delete("1.0", "end")
                if quote_data["special_notes"]:
                    self.notes_entry.insert("1.0", quote_data["special_notes"])

                self.round_off_entry.delete(0, "end")
                self.round_off_entry.insert(0, f"{quote_data['round_off']:.2f}")

                t_mode = quote_data.get("tax_mode", "exclusive")
                if t_mode == "inclusive":
                    self.global_tax_combo.set("Incl. 18% Tax (18% GST included)")
                else:
                    self.global_tax_combo.set("Excl. 18% Tax (+18% GST added)")

                # Load areas
                for a in quote_data["areas"]:
                    self.add_area(a["area_name"], area_data=a)
        else:
            # New quotation: generate sequential number
            new_q_num = QuotationService.generate_next_quotation_number()
            self.quote_num_entry.delete(0, "end")
            self.quote_num_entry.insert(0, new_q_num)

            if hasattr(self, "assisted_combo"):
                self.assisted_combo.set("None (Solo Sale)")
                self.assisted_share_pct_entry.delete(0, "end")
                self.assisted_share_amt_entry.delete(0, "end")

            # Add default initial areas: "Ground Floor" & "Kids Bathroom"
            self.add_area("GROUND FLOOR - LIVING ROOM")
            self.add_area("KIDS BATHROOM")

        self.recalculate_totals()

    def on_global_tax_changed(self, chosen_val=None):
        self.apply_global_tax_to_all_items()

    def apply_global_tax_to_all_items(self):
        is_incl = "Incl" in self.global_tax_combo.get()
        new_val = "Incl. 18%" if is_incl else "Excl. 18%"
        for aw in self.area_widgets:
            aw.default_tax_mode = "inclusive" if is_incl else "exclusive"
            for iw in aw.item_widgets:
                iw.tax_combo.set(new_val)
        self.recalculate_totals()

    def add_area(self, area_name: str, area_data=None):
        is_incl = "Incl" in self.global_tax_combo.get() if hasattr(self, "global_tax_combo") else False
        area_widget = AreaSectionWidget(
            self.areas_container,
            area_name=area_name,
            on_recalc=self.recalculate_totals,
            on_remove_area=self.remove_area,
            area_data=area_data,
            catalog_context=self.catalog_context,
            default_tax_mode="inclusive" if is_incl else "exclusive"
        )
        area_widget.pack(fill="x", pady=6)
        self.area_widgets.append(area_widget)
        self.recalculate_totals()

    def remove_area(self, area_widget):
        if len(self.area_widgets) <= 1:
            msgbox.showwarning("Notice", "A quotation must have at least one area section.")
            return
        confirm = msgbox.askyesno("Remove Area", f"Remove section '{area_widget.name_entry.get()}' and its items?")
        if confirm:
            if area_widget in self.area_widgets:
                self.area_widgets.remove(area_widget)
                area_widget.destroy()
                self.recalculate_totals()

    def apply_customer(self, c, update_combo=True):
        if not c:
            return
        self.matched_customer_id = c.id
        formatted_combo_str = f"{c.name} ({c.mobile_number})"
        if update_combo:
            current_vals = list(self.customer_combo.cget("values") or [])
            if formatted_combo_str not in current_vals:
                current_vals.insert(0, formatted_combo_str)
                self.customer_combo.configure(values=current_vals)
            self.customer_combo.set(formatted_combo_str)

        self.phone_entry.delete(0, "end")
        self.phone_entry.insert(0, c.mobile_number)

        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, c.delivery_address or "")

        if c.site_location:
            self.project_name_entry.delete(0, "end")
            self.project_name_entry.insert(0, c.site_location)

        self.hide_customer_suggestions()
        self.update_customer_status(
            f"✓ Existing Customer: {c.name} — All details loaded from database",
            status_type="success"
        )

    def on_customer_selected(self, val):
        for c in self.customers_cache:
            if f"{c.name} ({c.mobile_number})" == val or c.name.strip() == val.strip():
                self.apply_customer(c, update_combo=False)
                break

    def search_customers(self, query: str):
        query = (query or "").strip()
        if not query:
            return []
        clean_digits = "".join(ch for ch in query if ch.isdigit())
        q_lower = query.lower()

        if not hasattr(self, "customers_cache") or not self.customers_cache:
            self.customers_cache = list(Customer.select().order_by(Customer.name))

        results = []
        for c in self.customers_cache:
            c_digits = "".join(ch for ch in (c.mobile_number or "") if ch.isdigit())
            matched = False

            # Match 1: Phone digits substring or exact 10 digits
            if clean_digits and len(clean_digits) >= 3:
                if clean_digits in c_digits or (len(clean_digits) >= 10 and clean_digits[-10:] in c_digits):
                    matched = True

            # Match 2: Name substring
            if not matched and q_lower in (c.name or "").lower():
                matched = True

            # Match 3: Project / Site location
            if not matched and c.site_location and q_lower in c.site_location.lower():
                matched = True

            # Match 4: Delivery address
            if not matched and c.delivery_address and q_lower in c.delivery_address.lower():
                matched = True

            if matched:
                results.append(c)
        return results

    def _on_phone_key_release(self, event=None):
        if event and event.keysym in ("Return", "Tab", "Escape", "Up", "Down"):
            if event.keysym == "Return":
                if hasattr(self, "_current_cust_matches") and self._current_cust_matches:
                    self.apply_customer(self._current_cust_matches[0])
                    return
            elif event.keysym == "Escape":
                self.hide_customer_suggestions()
                return
            return

        val = self.phone_entry.get().strip()
        clean_digits = "".join(ch for ch in val if ch.isdigit())

        if not val or len(clean_digits) < 3:
            self.hide_customer_suggestions()
            if not val:
                self.update_customer_status("ℹ Enter mobile number or customer name to search database records", status_type="info")
            return

        matches = self.search_customers(val)
        if matches:
            # If exact 10-digit phone match, auto-fill immediately!
            if len(clean_digits) >= 10:
                for c in matches:
                    c_digits = "".join(ch for ch in (c.mobile_number or "") if ch.isdigit())
                    if clean_digits == c_digits or clean_digits[-10:] == c_digits[-10:]:
                        self.apply_customer(c)
                        return

            self.show_customer_suggestions(matches, search_term=val)
        else:
            self.hide_customer_suggestions()
            self.update_customer_status(f"✨ New Contact: '{val}' — Will be registered as new customer in database.", status_type="warning")

    def _on_phone_return(self, event=None):
        if hasattr(self, "_current_cust_matches") and self._current_cust_matches:
            self.apply_customer(self._current_cust_matches[0])

    def _on_customer_key_release(self, event=None):
        if event and event.keysym in ("Return", "Tab", "Escape", "Up", "Down"):
            if event.keysym == "Return":
                if hasattr(self, "_current_cust_matches") and self._current_cust_matches:
                    self.apply_customer(self._current_cust_matches[0])
                    return
            elif event.keysym == "Escape":
                self.hide_customer_suggestions()
                return
            return

        val = self.customer_combo.get().strip()
        if not val or len(val) < 2:
            self.hide_customer_suggestions()
            return

        matches = self.search_customers(val)
        if matches:
            for c in matches:
                if c.name.strip().lower() == val.lower() or f"{c.name} ({c.mobile_number})".lower() == val.lower():
                    self.apply_customer(c, update_combo=False)
                    return
            self.show_customer_suggestions(matches, search_term=val)
        else:
            self.hide_customer_suggestions()
            self.update_customer_status(f"✨ New Customer Name: '{val}' — Will be registered in database upon quotation save.", status_type="warning")

    def show_customer_suggestions(self, matches, search_term=""):
        self._current_cust_matches = matches
        for w in self.cust_suggestions_card.winfo_children():
            w.destroy()

        self.cust_suggestions_card.grid(row=2, column=0, columnspan=4, padx=6, pady=(4, 8), sticky="ew")

        # Header bar of suggestions popup
        h_row = ctk.CTkFrame(self.cust_suggestions_card, fg_color="transparent")
        h_row.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            h_row,
            text=f"🔍 Found {len(matches)} Existing Customer(s) in Database matching '{search_term}':",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(side="left")

        close_btn = ctk.CTkButton(
            h_row,
            text="✕ Dismiss",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9),
            width=60,
            height=20,
            corner_radius=Theme.RADIUS_PILL,
            fg_color="transparent",
            text_color=("#615D56", "#A8A297"),
            hover_color=("#E5E7EB", "#374151"),
            command=self.hide_customer_suggestions
        )
        close_btn.pack(side="right")

        # Results (up to 4 matches displayed)
        for c in matches[:4]:
            rf = ctk.CTkFrame(self.cust_suggestions_card, fg_color=("#FFFFFF", "#1E1C1A"), corner_radius=8, border_width=1, border_color=Theme.LIGHT_BORDER)
            rf.pack(fill="x", padx=10, pady=3)

            info_f = ctk.CTkFrame(rf, fg_color="transparent")
            info_f.pack(side="left", padx=10, pady=6, fill="x", expand=True)

            top_line = f"👤 {c.name}    •    📞 {c.mobile_number}"
            ctk.CTkLabel(
                info_f,
                text=top_line,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=(Theme.BLACK, Theme.PAPER),
                anchor="w"
            ).pack(anchor="w")

            addr_text = f"📍 {c.delivery_address}" + (f"  |  🏗️ Site: {c.site_location}" if c.site_location else "")
            ctk.CTkLabel(
                info_f,
                text=addr_text[:90] + ("..." if len(addr_text) > 90 else ""),
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10),
                text_color=("#615D56", "#A8A297"),
                anchor="w"
            ).pack(anchor="w")

            # Action Auto-fill button
            fill_btn = ctk.CTkButton(
                rf,
                text="Auto-Fill Details ✓",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                corner_radius=Theme.RADIUS_PILL,
                width=130,
                height=26,
                command=lambda cust=c: self.apply_customer(cust)
            )
            fill_btn.pack(side="right", padx=10, pady=6)

    def hide_customer_suggestions(self):
        self._current_cust_matches = []
        if hasattr(self, "cust_suggestions_card") and self.cust_suggestions_card.winfo_manager() == "grid":
            self.cust_suggestions_card.grid_remove()

    def clear_customer_fields(self):
        self.matched_customer_id = None
        self.customer_combo.set("")
        self.phone_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.project_name_entry.delete(0, "end")
        self.hide_customer_suggestions()
        self.update_customer_status("ℹ Cleared. Start typing phone number or customer name to search database.", status_type="info")

    def update_customer_status(self, text, status_type="info"):
        color = Theme.SUCCESS if status_type == "success" else (Theme.WARNING if status_type == "warning" else ("#615D56", "#A8A297"))
        self.cust_status_lbl.configure(text=text, text_color=color)

    def refresh_customer_dropdown_options(self):
        self.customers_cache = list(Customer.select().order_by(Customer.name))
        cust_names = [f"{c.name} ({c.mobile_number})" for c in self.customers_cache]
        self.customer_combo.configure(values=cust_names)

    def open_quick_customer_modal(self):
        # Quick modal dialog to add customer
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Customer")
        dialog.geometry("450x380")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Quick New Customer", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 12))

        f = ctk.CTkFrame(dialog, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(f, text="Customer Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        name_ent = ctk.CTkEntry(f, placeholder_text="e.g. Ar. Sameer Khan")
        name_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Mobile Number:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        phone_ent = ctk.CTkEntry(f, placeholder_text="+91 98xxx xxxxx")
        phone_ent.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(f, text="Delivery / Site Address:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        addr_ent = ctk.CTkEntry(f, placeholder_text="Site location details")
        addr_ent.pack(fill="x", pady=(2, 12))

        def save_quick_cust():
            cname = name_ent.get().strip()
            cphone = phone_ent.get().strip()
            caddr = addr_ent.get().strip()
            if not cname or not cphone:
                msgbox.showwarning("Incomplete", "Please enter customer name and phone.", parent=dialog)
                return
            new_c = Customer.create(name=cname, mobile_number=cphone, delivery_address=caddr)
            self.customers_cache.append(new_c)
            self.refresh_customer_dropdown_options()
            self.apply_customer(new_c)
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="Save Customer",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=save_quick_cust
        ).pack(pady=(0, 20))

    def _get_current_gross_total(self) -> float:
        total_gross = 0.0
        for aw in getattr(self, "area_widgets", []):
            adata = aw.get_data()
            for it in adata.get("items", []):
                taxable = it.get("taxable_amount")
                gst = it.get("gst_amount")
                line_gross = it.get("line_gross")
                if line_gross is None:
                    tot = it.get("total_amount", 0.0)
                    t_mode = it.get("tax_mode", "exclusive")
                    if t_mode == "exclusive":
                        taxable = tot
                        gst = round(taxable * 0.18, 2)
                        line_gross = round(taxable + gst, 2)
                    else:
                        line_gross = tot
                total_gross += line_gross
        return round(total_gross, 2)

    def _on_discount_target_key(self, event=None):
        if getattr(self, "_syncing_discount_inputs", False):
            return
        self._syncing_discount_inputs = True
        try:
            val_str = self.discount_target_entry.get().strip()
            if not val_str:
                self.discount_val_entry.delete(0, "end")
                self.discount_pct_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(text="")
                return
            target = float(val_str)
            curr_gross = self._get_current_gross_total()
            if curr_gross > 0 and target <= curr_gross:
                disc_amt = curr_gross - target
                disc_pct = (disc_amt / curr_gross) * 100.0
                self.discount_val_entry.delete(0, "end")
                self.discount_val_entry.insert(0, f"{disc_amt:.2f}")
                self.discount_pct_entry.delete(0, "end")
                self.discount_pct_entry.insert(0, f"{disc_pct:.2f}")
                self.discount_feedback_lbl.configure(
                    text=f"Target: ₹{target:,.2f}  |  Discount: -₹{disc_amt:,.2f} ({disc_pct:.2f}%) to be distributed",
                    text_color=Theme.PRIMARY
                )
            elif curr_gross > 0 and target > curr_gross:
                self.discount_val_entry.delete(0, "end")
                self.discount_pct_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(
                    text=f"Target ₹{target:,.2f} exceeds current total ₹{curr_gross:,.2f}",
                    text_color=Theme.WARNING
                )
            else:
                self.discount_val_entry.delete(0, "end")
                self.discount_pct_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(text="")
        except ValueError:
            pass
        finally:
            self._syncing_discount_inputs = False

    def _on_discount_val_key(self, event=None):
        if getattr(self, "_syncing_discount_inputs", False):
            return
        self._syncing_discount_inputs = True
        try:
            val_str = self.discount_val_entry.get().strip()
            if not val_str:
                self.discount_target_entry.delete(0, "end")
                self.discount_pct_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(text="")
                return
            disc_amt = float(val_str)
            curr_gross = self._get_current_gross_total()
            if curr_gross > 0:
                target = max(0.0, curr_gross - disc_amt)
                disc_pct = (disc_amt / curr_gross) * 100.0
                self.discount_target_entry.delete(0, "end")
                self.discount_target_entry.insert(0, f"{target:.2f}")
                self.discount_pct_entry.delete(0, "end")
                self.discount_pct_entry.insert(0, f"{disc_pct:.2f}")
                self.discount_feedback_lbl.configure(
                    text=f"Discount: -₹{disc_amt:,.2f} ({disc_pct:.2f}%)  |  Target: ₹{target:,.2f}",
                    text_color=Theme.PRIMARY
                )
            else:
                self.discount_target_entry.delete(0, "end")
                self.discount_pct_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(text="")
        except ValueError:
            pass
        finally:
            self._syncing_discount_inputs = False

    def _on_discount_pct_key(self, event=None):
        if getattr(self, "_syncing_discount_inputs", False):
            return
        self._syncing_discount_inputs = True
        try:
            val_str = self.discount_pct_entry.get().strip()
            if not val_str:
                self.discount_target_entry.delete(0, "end")
                self.discount_val_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(text="")
                return
            disc_pct = float(val_str)
            curr_gross = self._get_current_gross_total()
            if curr_gross > 0:
                disc_amt = round(curr_gross * (disc_pct / 100.0), 2)
                target = max(0.0, curr_gross - disc_amt)
                self.discount_target_entry.delete(0, "end")
                self.discount_target_entry.insert(0, f"{target:.2f}")
                self.discount_val_entry.delete(0, "end")
                self.discount_val_entry.insert(0, f"{disc_amt:.2f}")
                self.discount_feedback_lbl.configure(
                    text=f"Discount: {disc_pct:.2f}% (-₹{disc_amt:,.2f})  |  Target: ₹{target:,.2f}",
                    text_color=Theme.PRIMARY
                )
            else:
                self.discount_target_entry.delete(0, "end")
                self.discount_val_entry.delete(0, "end")
                self.discount_feedback_lbl.configure(text="")
        except ValueError:
            pass
        finally:
            self._syncing_discount_inputs = False

    def clear_discount_inputs(self):
        self._syncing_discount_inputs = True
        try:
            self.discount_target_entry.delete(0, "end")
            self.discount_val_entry.delete(0, "end")
            self.discount_pct_entry.delete(0, "end")
            self.discount_feedback_lbl.configure(text="")
        finally:
            self._syncing_discount_inputs = False

    def apply_distributed_discount(self):
        # 1. Collect all active items
        active_items = []
        for aw in self.area_widgets:
            for iw in aw.item_widgets:
                d = iw.get_data()
                has_content = (
                    bool(d.get("description", "").strip()) or
                    d.get("quantity_sqft", 0.0) > 0 or
                    d.get("quantity_boxes", 0.0) > 0 or
                    d.get("rate_per_sqft", 0.0) > 0 or
                    d.get("rate_per_box", 0.0) > 0 or
                    d.get("total_amount", 0.0) > 0
                )
                if has_content and (d.get("total_amount", 0.0) > 0 or d.get("line_gross", 0.0) > 0):
                    active_items.append((aw, iw))

        if not active_items:
            msgbox.showwarning("No Items", "Please add quotation items with valid quantities and rates first.")
            return

        curr_gross = sum(iw.get_data().get("line_gross", 0.0) for _, iw in active_items)
        if curr_gross <= 0:
            msgbox.showwarning("Zero Total", "Current quotation gross total is ₹0.00. Cannot apply discount.")
            return

        # 2. Determine target
        target_str = self.discount_target_entry.get().strip()
        val_str = self.discount_val_entry.get().strip()
        pct_str = self.discount_pct_entry.get().strip()

        target_total = None
        if target_str:
            try:
                target_total = float(target_str)
            except ValueError:
                pass
        elif val_str:
            try:
                disc_amt = float(val_str)
                target_total = curr_gross - disc_amt
            except ValueError:
                pass
        elif pct_str:
            try:
                disc_pct = float(pct_str)
                target_total = curr_gross * (1.0 - disc_pct / 100.0)
            except ValueError:
                pass

        if target_total is None:
            msgbox.showwarning("Input Required", "Please enter Target Total (₹), Discount (₹), or Discount (%).")
            return

        if target_total <= 0:
            msgbox.showerror("Invalid Value", "Target total must be greater than zero.")
            return

        if target_total > curr_gross:
            confirm = msgbox.askyesno(
                "Target Higher Than Current",
                f"Target total (₹ {target_total:,.2f}) is greater than current total (₹ {curr_gross:,.2f}).\n\nDo you want to adjust prices upward?"
            )
            if not confirm:
                return

        disc_amount = curr_gross - target_total
        disc_percentage = (disc_amount / curr_gross) * 100.0
        factor = target_total / curr_gross

        # 3. Apply discount factor to each item row
        for _, iw in active_items:
            iw.apply_discount_factor(factor)

        # 4. Check for rounding discrepancy on the line_gross sum
        new_gross = sum(iw.get_data().get("line_gross", 0.0) for _, iw in active_items)
        gross_diff = round(target_total - new_gross, 2)
        if abs(gross_diff) > 0 and active_items:
            last_aw, last_iw = active_items[-1]
            tax_str = last_iw.tax_combo.get().strip() if hasattr(last_iw, "tax_combo") else "Excl. 18%"
            is_incl = "Incl" in tax_str
            try:
                current_last_tot = float(last_iw.total_entry.get().strip() or 0.0)
                if is_incl:
                    adj_tot = round(current_last_tot + gross_diff, 2)
                else:
                    adj_tot = round(current_last_tot + (gross_diff / 1.18), 2)

                if adj_tot > 0:
                    last_iw.total_entry.delete(0, "end")
                    last_iw.total_entry.insert(0, f"{adj_tot:.2f}")

                    sqft = float(last_iw.sqft_entry.get().strip() or 0.0)
                    cov = float(last_iw.cov_entry.get().strip() or 0.0)
                    boxes = float(last_iw.box_entry.get().strip() or 0.0)
                    if sqft > 0:
                        r_sqft = round(adj_tot / sqft, 2)
                        last_iw.rate_sqft_entry.delete(0, "end")
                        last_iw.rate_sqft_entry.insert(0, f"{r_sqft:.2f}")
                        if cov > 0:
                            last_iw.rate_box_entry.delete(0, "end")
                            last_iw.rate_box_entry.insert(0, f"{round(r_sqft * cov, 2):.2f}")
                    elif boxes > 0:
                        r_box = round(adj_tot / boxes, 2)
                        last_iw.rate_box_entry.delete(0, "end")
                        last_iw.rate_box_entry.insert(0, f"{r_box:.2f}")
            except Exception:
                pass

        # 5. Clear round off entry to 0.00 so no discount row appears at bottom or in PDF
        self.round_off_entry.delete(0, "end")
        self.round_off_entry.insert(0, "0.00")

        # 6. Recalculate all area subtotals & editor totals
        for aw in self.area_widgets:
            aw.on_item_recalc()
        self.recalculate_totals()

        # 7. Update UI feedback
        self.discount_feedback_lbl.configure(
            text=f"✓ Distributed {disc_percentage:.2f}% discount (-₹{disc_amount:,.2f}) across all items.\nTarget ₹{target_total:,.2f} achieved with clean 0.00 round off.",
            text_color=Theme.SUCCESS
        )

        msgbox.showinfo(
            "Discount Distributed Successfully",
            f"A discount of ₹ {disc_amount:,.2f} ({disc_percentage:.2f}%) was distributed across {len(active_items)} item(s).\n\n"
            f"• Original Quote: ₹ {curr_gross:,.2f}\n"
            f"• New Target Total: ₹ {target_total:,.2f}\n"
            f"• All item sqft/box rates have been updated directly.\n"
            f"• No separate discount row will appear in totals or the exported PDF."
        )

    def _get_current_net_total(self) -> float:
        """Returns the current computed net payable total from editor."""
        try:
            txt = self.net_total_lbl.cget("text")
            clean = txt.replace("₹", "").replace(",", "").strip()
            return float(clean or 0.0)
        except Exception:
            return 0.0

    def _on_primary_salesperson_changed(self, choice=None):
        """Called when primary salesperson changes."""
        if hasattr(self, "assisted_combo"):
            asst = self.assisted_combo.get().strip()
            if asst and not asst.startswith("None") and asst == self.salesperson_combo.get().strip():
                msgbox.showwarning("Notice", "Lead Sales Associate and Assisted Sales Associate cannot be the same person.")
                self.assisted_combo.set("None (Solo Sale)")
        self._update_split_display()

    def _on_assisted_salesperson_changed(self, choice=None):
        """Called when assisted salesperson dropdown changes."""
        if not hasattr(self, "assisted_combo"):
            return
        asst = self.assisted_combo.get().strip()
        if asst and not asst.startswith("None"):
            if asst == self.salesperson_combo.get().strip():
                msgbox.showwarning("Notice", "Lead Sales Associate and Assisted Sales Associate cannot be the same person.")
                self.assisted_combo.set("None (Solo Sale)")
                self._update_split_display()
                return
            # If entries empty, default to 50%
            if not self.assisted_share_pct_entry.get().strip():
                self.assisted_share_pct_entry.insert(0, "50.0")
        self._update_split_display()

    def _on_split_mode_changed(self, choice=None):
        """Called when split mode changes between Percentage and Amount."""
        self._update_split_display()

    def _on_assisted_pct_key(self, event=None):
        """Synchronizes amount when percentage is typed."""
        if getattr(self, "_syncing_split_entries", False):
            return
        net_tot = self._get_current_net_total()
        self._syncing_split_entries = True
        try:
            pct_str = self.assisted_share_pct_entry.get().strip()
            if not pct_str:
                self.assisted_share_amt_entry.delete(0, "end")
                self.assisted_share_amt_entry.insert(0, "0.00")
            else:
                pct = float(pct_str)
                amt = round(net_tot * (pct / 100.0), 2)
                self.assisted_share_amt_entry.delete(0, "end")
                self.assisted_share_amt_entry.insert(0, f"{amt:.2f}")
        except ValueError:
            pass
        finally:
            self._syncing_split_entries = False
        self._update_split_preview_label()

    def _on_assisted_amt_key(self, event=None):
        """Synchronizes percentage when amount is typed."""
        if getattr(self, "_syncing_split_entries", False):
            return
        net_tot = self._get_current_net_total()
        self._syncing_split_entries = True
        try:
            amt_str = self.assisted_share_amt_entry.get().strip()
            if not amt_str:
                self.assisted_share_pct_entry.delete(0, "end")
                self.assisted_share_pct_entry.insert(0, "0.0")
            else:
                amt = float(amt_str)
                pct = round((amt / net_tot * 100.0), 1) if net_tot > 0 else 0.0
                self.assisted_share_pct_entry.delete(0, "end")
                self.assisted_share_pct_entry.insert(0, f"{pct:.1f}")
        except ValueError:
            pass
        finally:
            self._syncing_split_entries = False
        self._update_split_preview_label()

    def set_equal_split(self):
        """Sets equal 50/50 split between lead and assisted salesperson."""
        if not hasattr(self, "assisted_combo"):
            return
        asst = self.assisted_combo.get().strip()
        if not asst or asst.startswith("None"):
            # Select first available non-primary salesperson
            prim = self.salesperson_combo.get().strip()
            vals = self.assisted_combo.cget("values") or []
            for v in vals:
                if not v.startswith("None") and v != prim:
                    self.assisted_combo.set(v)
                    break
        self.split_mode_combo.set("Percentage (%)")
        self.assisted_share_pct_entry.delete(0, "end")
        self.assisted_share_pct_entry.insert(0, "50.0")
        self._update_split_display()

    def _update_split_display(self):
        """Recalculates amounts and updates preview label."""
        if not hasattr(self, "assisted_combo"):
            return
        asst = self.assisted_combo.get().strip()
        if not asst or asst.startswith("None"):
            self.split_preview_lbl.configure(
                text="ℹ Solo Sale: 100% of quotation value is attributed to the lead sales associate.",
                text_color=("#615D56", "#A8A297")
            )
            return

        net_tot = self._get_current_net_total()
        is_pct = "Percentage" in self.split_mode_combo.get()

        if is_pct:
            pct_txt = self.assisted_share_pct_entry.get().strip()
            try:
                pct = float(pct_txt) if pct_txt else 50.0
            except ValueError:
                pct = 50.0
            amt = round(net_tot * (pct / 100.0), 2)
            if not getattr(self, "_syncing_split_entries", False):
                self._syncing_split_entries = True
                try:
                    self.assisted_share_amt_entry.delete(0, "end")
                    self.assisted_share_amt_entry.insert(0, f"{amt:.2f}")
                finally:
                    self._syncing_split_entries = False
        else:
            amt_txt = self.assisted_share_amt_entry.get().strip()
            try:
                amt = float(amt_txt) if amt_txt else round(net_tot * 0.5, 2)
            except ValueError:
                amt = round(net_tot * 0.5, 2)
            pct = round((amt / net_tot * 100.0), 1) if net_tot > 0 else 50.0
            if not getattr(self, "_syncing_split_entries", False):
                self._syncing_split_entries = True
                try:
                    self.assisted_share_pct_entry.delete(0, "end")
                    self.assisted_share_pct_entry.insert(0, f"{pct:.1f}")
                finally:
                    self._syncing_split_entries = False

        self._update_split_preview_label()

    def _update_split_preview_label(self):
        if not hasattr(self, "split_preview_lbl"):
            return
        asst = self.assisted_combo.get().strip() if hasattr(self, "assisted_combo") else "None"
        if not asst or asst.startswith("None"):
            self.split_preview_lbl.configure(
                text="ℹ Solo Sale: 100% of quotation value is attributed to the lead sales associate.",
                text_color=("#615D56", "#A8A297")
            )
            return

        net_tot = self._get_current_net_total()
        lead_name = self.salesperson_combo.get().split("(")[0].strip() or "Lead"
        asst_name = asst.split("(")[0].strip() or "Assisted"

        try:
            asst_pct = float(self.assisted_share_pct_entry.get().strip() or 0.0)
        except ValueError:
            asst_pct = 0.0

        try:
            asst_amt = float(self.assisted_share_amt_entry.get().strip() or 0.0)
        except ValueError:
            asst_amt = 0.0

        lead_pct = max(0.0, round(100.0 - asst_pct, 1))
        lead_amt = max(0.0, round(net_tot - asst_amt, 2))

        self.split_preview_lbl.configure(
            text=f"✓ Split Active: Lead ({lead_name}) gets {lead_pct:.1f}% (₹ {lead_amt:,.2f})  •  Assisted ({asst_name}) gets {asst_pct:.1f}% (₹ {asst_amt:,.2f})",
            text_color=Theme.PRIMARY
        )

    def recalculate_totals(self):
        total_taxable = 0.0
        total_gst = 0.0
        gross = 0.0
        for aw in self.area_widgets:
            adata = aw.get_data()
            for it in adata["items"]:
                taxable = it.get("taxable_amount")
                gst = it.get("gst_amount")
                line_gross = it.get("line_gross")
                if taxable is None or gst is None or line_gross is None:
                    tot = it.get("total_amount", 0.0)
                    t_mode = it.get("tax_mode", "exclusive")
                    if t_mode == "exclusive":
                        taxable = tot
                        gst = round(taxable * 0.18, 2)
                        line_gross = round(taxable + gst, 2)
                    else:
                        line_gross = tot
                        taxable = round(line_gross / 1.18, 2)
                        gst = round(line_gross - taxable, 2)

                total_taxable += taxable
                total_gst += gst
                gross += line_gross

        cgst = round(total_gst / 2.0, 2)
        sgst = round(total_gst - cgst, 2)

        try:
            round_off = float(self.round_off_entry.get().strip() or 0.0)
        except ValueError:
            round_off = 0.0

        net = round(gross + round_off, 2)
        self.taxable_subtotal_lbl.configure(text=f"₹ {total_taxable:,.2f}")
        self.cgst_lbl.configure(text=f"₹ {cgst:,.2f}")
        self.sgst_lbl.configure(text=f"₹ {sgst:,.2f}")
        self.total_gst_lbl.configure(text=f"₹ {total_gst:,.2f}")
        self.gross_total_lbl.configure(text=f"₹ {gross:,.2f}")
        self.net_total_lbl.configure(text=f"₹ {net:,.2f}")
        self._update_split_display()

    def collect_quotation_payload(self):
        # Validate customer
        selected_cust_str = self.customer_combo.get().strip()
        matched_cust = None
        if hasattr(self, "matched_customer_id") and self.matched_customer_id:
            try:
                matched_cust = Customer.get_by_id(self.matched_customer_id)
            except Customer.DoesNotExist:
                matched_cust = None

        if not matched_cust:
            for c in self.customers_cache:
                if f"{c.name} ({c.mobile_number})" == selected_cust_str or c.name.strip().lower() == selected_cust_str.lower():
                    matched_cust = c
                    break

        phone_val = self.phone_entry.get().strip()
        if not matched_cust and phone_val:
            clean_digits = "".join(d for d in phone_val if d.isdigit())
            for c in self.customers_cache:
                c_digits = "".join(d for d in (c.mobile_number or "") if d.isdigit())
                if clean_digits and (clean_digits == c_digits or (len(clean_digits) >= 10 and clean_digits[-10:] == c_digits[-10:])):
                    matched_cust = c
                    break

        # If still not matched, auto-create the new customer in database!
        if not matched_cust:
            cust_name = selected_cust_str or "Valued Client"
            if not phone_val:
                raise ValueError("Please enter a customer contact phone number or select an existing customer.")
            deliv_addr = self.address_entry.get().strip() or "Standard Site Delivery"
            proj_name = self.project_name_entry.get().strip() or None
            matched_cust = Customer.create(
                name=cust_name,
                mobile_number=phone_val,
                delivery_address=deliv_addr,
                site_location=proj_name
            )
            self.customers_cache.append(matched_cust)
            self.refresh_customer_dropdown_options()
            self.matched_customer_id = matched_cust.id

        # Validate primary salesperson
        selected_sp_str = self.salesperson_combo.get()
        matched_sp = None
        for s in self.salespersons_cache:
            if f"{s.name} ({s.role})" == selected_sp_str:
                matched_sp = s
                break
        if not matched_sp:
            raise ValueError("Please select a sales associate.")

        # Validate assisted salesperson & split share
        assisted_choice = self.assisted_combo.get().strip() if hasattr(self, "assisted_combo") else "None"
        matched_assisted = None
        split_type = "none"
        assisted_share_value = 0.0

        if assisted_choice and not assisted_choice.startswith("None"):
            for s in self.salespersons_cache:
                if f"{s.name} ({s.role})" == assisted_choice or s.name == assisted_choice:
                    matched_assisted = s
                    break
            if not matched_assisted:
                raise ValueError("Selected assisted salesperson is not recognized.")
            if matched_assisted.id == matched_sp.id:
                raise ValueError("Lead Sales Associate and Assisted Sales Associate cannot be the same person.")

            mode_str = self.split_mode_combo.get()
            split_type = "percentage" if "Percentage" in mode_str else "amount"

            if split_type == "percentage":
                pct_txt = self.assisted_share_pct_entry.get().strip()
                if not pct_txt:
                    pct_txt = "50.0"
                try:
                    val = float(pct_txt)
                    if val <= 0 or val >= 100:
                        raise ValueError()
                    assisted_share_value = val
                except ValueError:
                    raise ValueError("Assisted salesperson share percentage must be a number between 0% and 100%.")
            else:
                amt_txt = self.assisted_share_amt_entry.get().strip()
                if not amt_txt:
                    raise ValueError("Please enter an assisted salesperson share amount.")
                try:
                    val = float(amt_txt)
                    if val <= 0:
                        raise ValueError()
                    assisted_share_value = val
                except ValueError:
                    raise ValueError("Assisted salesperson share amount must be a positive number.")

        try:
            round_off = float(self.round_off_entry.get().strip() or 0.0)
        except ValueError:
            round_off = 0.0

        areas_data = []
        for aw in self.area_widgets:
            ad = aw.get_data()
            if ad["items"]:
                areas_data.append(ad)

        if not areas_data:
            raise ValueError("Quotation must contain at least one item with valid quantity and rate.")

        tax_mode = "inclusive" if "Incl" in self.global_tax_combo.get() else "exclusive"

        return {
            "id": self.quote_id,
            "quotation_number": self.quote_num_entry.get().strip(),
            "quotation_date": self.date_entry.get().strip() or date.today(),
            "customer_id": matched_cust.id,
            "sales_person_id": matched_sp.id,
            "assisted_by_id": matched_assisted.id if matched_assisted else None,
            "split_type": split_type,
            "assisted_share_value": assisted_share_value,
            "project_name": self.project_name_entry.get().strip(),
            "special_notes": self.notes_entry.get("1.0", "end").strip(),
            "status": self.status_combo.get(),
            "tax_mode": tax_mode,
            "round_off": round_off,
            "areas": areas_data,
        }

    def save_quotation(self):
        try:
            payload = self.collect_quotation_payload()
            quote = QuotationService.save_quotation(payload)
            self.quote_id = quote.id
            self.title_lbl.configure(text=f"Editing Quotation: {quote.quotation_number}")
            msgbox.showinfo(
                "Saved Successfully",
                f"Quotation {quote.quotation_number} saved successfully!\nNet Total: ₹ {quote.net_total:,.2f}"
            )
            return quote
        except Exception as e:
            msgbox.showerror("Validation Error", str(e))
            return None

    def save_and_export_pdf(self):
        quote = self.save_quotation()
        if quote:
            try:
                pdf_path = CeramicPDFGenerator.generate_quotation_pdf(quote.id)
                msgbox.showinfo(
                    "PDF Generated",
                    f"Quotation PDF generated successfully!\n\nLocation:\n{pdf_path}"
                )
                try:
                    import os
                    os.startfile(pdf_path)
                except Exception:
                    pass
            except Exception as e:
                msgbox.showerror("PDF Export Error", f"Failed to generate PDF:\n{str(e)}")
