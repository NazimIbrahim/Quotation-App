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

        # 11 columns in grid:
        # 0: Sl (weight 1)
        # 1: Description (weight 5)
        # 2: Size (weight 2)
        # 3: Brand (weight 3)
        # 4: Coverage Area (Sqft/Box) (weight 2)
        # 5: Qty Sqft (weight 2)
        # 6: Rate Sqft (weight 2)
        # 7: Qty Box (weight 2)
        # 8: Rate Box (weight 2)
        # 9: Total Amount (weight 2)
        # 10: Delete (weight 1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)
        self.grid_columnconfigure(2, weight=2)
        self.grid_columnconfigure(3, weight=3)
        self.grid_columnconfigure(4, weight=2)
        self.grid_columnconfigure(5, weight=2)
        self.grid_columnconfigure(6, weight=2)
        self.grid_columnconfigure(7, weight=2)
        self.grid_columnconfigure(8, weight=2)
        self.grid_columnconfigure(9, weight=2)
        self.grid_columnconfigure(10, weight=1)

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

        # 7. Quantity in Boxes
        self.box_entry = ctk.CTkEntry(
            self,
            placeholder_text="Boxes",
            height=28,
            width=60,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("quantity_boxes"):
            self.box_entry.insert(0, str(data["quantity_boxes"]))
        self.box_entry.grid(row=0, column=7, padx=2, pady=3, sticky="ew")
        self.box_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("box"))

        # 8. Rate per Box
        self.rate_box_entry = ctk.CTkEntry(
            self,
            placeholder_text="₹/Box",
            height=28,
            width=60,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11)
        )
        if data.get("rate_per_box"):
            self.rate_box_entry.insert(0, str(data["rate_per_box"]))
        self.rate_box_entry.grid(row=0, column=8, padx=2, pady=3, sticky="ew")
        self.rate_box_entry.bind("<KeyRelease>", lambda e: self.recalculate_amount("rate_box"))

        # 9. Total Amount Entry
        self.total_entry = ctk.CTkEntry(
            self,
            placeholder_text="Total ₹",
            height=28,
            width=75,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold")
        )
        if data.get("total_amount"):
            self.total_entry.insert(0, f"{float(data['total_amount']):.2f}")
        self.total_entry.grid(row=0, column=9, padx=2, pady=3, sticky="ew")
        self.total_entry.bind("<KeyRelease>", lambda e: self.on_recalc())

        # 10. Delete Button
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
        del_btn.grid(row=0, column=10, padx=2, pady=3)

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

            if trigger_source == "sqft":
                if cov > 0 and q_sqft > 0:
                    q_box = round(q_sqft / cov, 2)
                    self.box_entry.delete(0, "end")
                    self.box_entry.insert(0, f"{q_box:g}")
                if cov > 0 and r_sqft > 0 and (r_box == 0 or not rate_box_txt):
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

        return {
            "sl_no": self.sl_no,
            "description": self.desc_entry.get().strip(),
            "size": self.size_combo.get().strip(),
            "brand": self.brand_combo.get().strip(),
            "coverage_area": cov,
            "quantity_sqft": sqft,
            "rate_per_sqft": r_sqft,
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
        super().__init__(
            master,
            corner_radius=10,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=1,
            border_color=("#CBD5E1", "#334155"),
            **kwargs
        )
        self.on_recalc = on_recalc
        self.on_remove_area = on_remove_area
        self.catalog_context = catalog_context or {}
        self.item_widgets = []

        # 1. Area Section Header
        self.header = ctk.CTkFrame(self, fg_color=("#0F172A", "#0B0F19"), corner_radius=8, height=36)
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
            height=26,
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
            width=90,
            height=24,
            fg_color="transparent",
            text_color=Theme.DANGER,
            hover_color=("#7F1D1D", "#450A0A"),
            command=self.remove_self
        )
        del_area_btn.pack(side="right", padx=10)

        # 2. Table Column Titles (10 columns matching PDF layout + Action button)
        col_bar = ctk.CTkFrame(self, fg_color=("#F1F5F9", "#111827"), height=26)
        col_bar.pack(fill="x", padx=8, pady=(2, 4))
        col_bar.grid_columnconfigure(0, weight=1)
        col_bar.grid_columnconfigure(1, weight=5)
        col_bar.grid_columnconfigure(2, weight=2)
        col_bar.grid_columnconfigure(3, weight=3)
        col_bar.grid_columnconfigure(4, weight=2)
        col_bar.grid_columnconfigure(5, weight=2)
        col_bar.grid_columnconfigure(6, weight=2)
        col_bar.grid_columnconfigure(7, weight=2)
        col_bar.grid_columnconfigure(8, weight=2)
        col_bar.grid_columnconfigure(9, weight=2)
        col_bar.grid_columnconfigure(10, weight=1)

        cols = [
            "Sl.",
            "Item Description",
            "Size",
            "Brand",
            "Cov (Sqft/Bx)",
            "Qty Sqft",
            "₹ / Sqft",
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
        self.items_container.pack(fill="x", padx=6, pady=(0, 6))

        # 4. Bottom Controls: "+ Add Item" & Area Subtotal
        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=10, pady=(2, 8))

        add_item_btn = ctk.CTkButton(
            bot_bar,
            text="+ Add Tile Item",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            width=110,
            height=26,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.add_item
        )
        add_item_btn.pack(side="left")

        self.area_subtotal_lbl = ctk.CTkLabel(
            bot_bar,
            text="Area Subtotal: ₹ 0.00",
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
            subtotal += d["total_amount"]
        self.area_subtotal_lbl.configure(text=f"Area Subtotal: ₹ {subtotal:,.2f}")
        self.on_recalc()

    def remove_self(self):
        if self.on_remove_area:
            self.on_remove_area(self)

    def get_data(self):
        items = []
        for w in self.item_widgets:
            d = w.get_data()
            if d["description"]:  # Skip completely blank lines
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
            fg_color=(Theme.STONE, "#2B2824"),
            text_color=(Theme.BLACK, Theme.PAPER),
            hover_color=Theme.PRIMARY,
            command=lambda: self.controller.show_view("quotations", None),
            height=34
        )
        back_btn.pack(side="left", padx=4)

        brand_cat_btn = ctk.CTkButton(
            btn_box,
            text="🏷️ Brands & Coverage",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=("#1E293B", "#334155"),
            text_color="#F8FAFC",
            hover_color=Theme.PRIMARY,
            command=lambda: self.controller.show_view("brand_catalog"),
            height=34
        )
        brand_cat_btn.pack(side="left", padx=4)

        sync_cat_btn = ctk.CTkButton(
            btn_box,
            text="🔄 Sync Catalog",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=("#334155", "#475569"),
            text_color="#F8FAFC",
            hover_color=Theme.PRIMARY,
            command=self.refresh_catalog_data,
            height=34
        )
        sync_cat_btn.pack(side="left", padx=4)

        save_pdf_btn = ctk.CTkButton(
            btn_box,
            text="📄 Save & Export PDF",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.ACCENT_GOLD,
            hover_color=Theme.ACCENT_GOLD_HOVER,
            command=self.save_and_export_pdf,
            height=34
        )
        save_pdf_btn.pack(side="left", padx=4)

        save_btn = ctk.CTkButton(
            btn_box,
            text="💾 Save Quotation",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.save_quotation,
            height=34
        )
        save_btn.pack(side="left", padx=4)

        # Scrollable container for full quotation document
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # 2. Header Card (Customer, Quotation No, Date, Sales Rep)
        header_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=12,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=1,
            border_color=(Theme.STONE, "#2B2824")
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

        # Customer Selector + Quick Add
        cust_label_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        cust_label_box.grid(row=0, column=2, padx=6, pady=(4, 2), sticky="ew")
        ctk.CTkLabel(cust_label_box, text="Customer:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        
        quick_cust_btn = ctk.CTkButton(
            cust_label_box,
            text="+ New Client",
            font=ctk.CTkFont(size=9, weight="bold"),
            width=70,
            height=18,
            fg_color="transparent",
            text_color=Theme.PRIMARY,
            command=self.open_quick_customer_modal
        )
        quick_cust_btn.pack(side="right")

        self.customer_combo = ctk.CTkComboBox(form_grid, values=["Loading..."], font=ctk.CTkFont(size=11), command=self.on_customer_selected)
        self.customer_combo.grid(row=1, column=2, padx=6, pady=(0, 8), sticky="ew")

        # Sales Person Selector
        ctk.CTkLabel(form_grid, text="Sales Associate:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, padx=6, pady=(4, 2), sticky="w")
        self.salesperson_combo = ctk.CTkComboBox(form_grid, values=["Loading..."], font=ctk.CTkFont(size=11))
        self.salesperson_combo.grid(row=1, column=3, padx=6, pady=(0, 8), sticky="ew")

        # Row 2: Contact, Project Name, Delivery Address
        ctk.CTkLabel(form_grid, text="Contact Phone:", font=ctk.CTkFont(size=11)).grid(row=2, column=0, padx=6, pady=(4, 2), sticky="w")
        self.phone_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11))
        self.phone_entry.grid(row=3, column=0, padx=6, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form_grid, text="Project / Site Name:", font=ctk.CTkFont(size=11)).grid(row=2, column=1, padx=6, pady=(4, 2), sticky="w")
        self.project_name_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11), placeholder_text="e.g. 4-BHK Villa / Bungalow")
        self.project_name_entry.grid(row=3, column=1, padx=6, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form_grid, text="Site / Delivery Address:", font=ctk.CTkFont(size=11)).grid(row=2, column=2, columnspan=2, padx=6, pady=(4, 2), sticky="w")
        self.address_entry = ctk.CTkEntry(form_grid, font=ctk.CTkFont(size=11), placeholder_text="Full delivery address for logistics")
        self.address_entry.grid(row=3, column=2, columnspan=2, padx=6, pady=(0, 8), sticky="ew")

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
                font=ctk.CTkFont(size=10),
                height=24,
                fg_color=(Theme.STONE, "#2B2824"),
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
            fg_color=("#F1F5F9", "#1E293B"),
            text_color=Theme.PRIMARY,
            hover_color=(Theme.STONE, "#2B2824"),
            border_width=1,
            border_color=Theme.PRIMARY,
            command=lambda: self.add_area("New Project Area"),
            height=32
        )
        add_custom_area_btn.pack(fill="x", pady=(0, 14))

        # 5. Bottom Financial Summary & Status Card
        totals_card = ctk.CTkFrame(
            self.scroll_body,
            corner_radius=12,
            fg_color=("#FFFFFF", "#201E1C"),
            border_width=1,
            border_color=(Theme.STONE, "#2B2824")
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
            width=200
        )
        self.status_combo.set("Open")
        self.status_combo.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            left_notes,
            text="Special Notes / Customer Remarks:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        self.notes_entry = ctk.CTkTextbox(left_notes, height=75, font=ctk.CTkFont(size=11))
        self.notes_entry.pack(fill="x")

        # Right: Financial Totals Box
        right_box = ctk.CTkFrame(t_layout, fg_color=(Theme.PAPER, "#1E1C1A"), corner_radius=10)
        right_box.grid(row=0, column=1, sticky="nsew")

        r_grid = ctk.CTkFrame(right_box, fg_color="transparent")
        r_grid.pack(fill="both", expand=True, padx=14, pady=12)
        r_grid.grid_columnconfigure(0, weight=1)
        r_grid.grid_columnconfigure(1, weight=1)

        # Gross Total
        ctk.CTkLabel(r_grid, text="Gross Total:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, pady=4, sticky="w")
        self.gross_total_lbl = ctk.CTkLabel(r_grid, text="₹ 0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.gross_total_lbl.grid(row=0, column=1, pady=4, sticky="e")

        # Round Off / Discount
        ctk.CTkLabel(r_grid, text="Round Off / Discount (±₹):", font=ctk.CTkFont(size=11)).grid(row=1, column=0, pady=4, sticky="w")
        self.round_off_entry = ctk.CTkEntry(r_grid, width=100, font=ctk.CTkFont(size=11))
        self.round_off_entry.insert(0, "0.00")
        self.round_off_entry.grid(row=1, column=1, pady=4, sticky="e")
        self.round_off_entry.bind("<KeyRelease>", lambda e: self.recalculate_totals())

        # Net Total
        ctk.CTkLabel(
            r_grid,
            text="NET PAYABLE TOTAL:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(Theme.BLACK, Theme.PAPER)
        ).grid(row=2, column=0, pady=(8, 4), sticky="w")

        self.net_total_lbl = ctk.CTkLabel(
            r_grid,
            text="₹ 0.00",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=Theme.ACCENT_GOLD
        )
        self.net_total_lbl.grid(row=2, column=1, pady=(8, 4), sticky="e")

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
            self.customer_combo.set(cust_names[0])
            self.on_customer_selected(cust_names[0])

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
                        break

                # Select salesperson
                for idx, s in enumerate(self.salespersons_cache):
                    if s.id == quote_data["sales_person_id"]:
                        self.salesperson_combo.set(sp_names[idx])
                        break

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

                # Load areas
                for a in quote_data["areas"]:
                    self.add_area(a["area_name"], area_data=a)
        else:
            # New quotation: generate sequential number
            new_q_num = QuotationService.generate_next_quotation_number()
            self.quote_num_entry.delete(0, "end")
            self.quote_num_entry.insert(0, new_q_num)

            # Add default initial areas: "Ground Floor" & "Kids Bathroom"
            self.add_area("GROUND FLOOR - LIVING ROOM")
            self.add_area("KIDS BATHROOM")

        self.recalculate_totals()

    def add_area(self, area_name: str, area_data=None):
        area_widget = AreaSectionWidget(
            self.areas_container,
            area_name=area_name,
            on_recalc=self.recalculate_totals,
            on_remove_area=self.remove_area,
            area_data=area_data,
            catalog_context=self.catalog_context
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

    def on_customer_selected(self, val):
        for c in self.customers_cache:
            if f"{c.name} ({c.mobile_number})" == val:
                self.phone_entry.delete(0, "end")
                self.phone_entry.insert(0, c.mobile_number)
                self.address_entry.delete(0, "end")
                self.address_entry.insert(0, c.delivery_address)
                if c.site_location and not self.project_name_entry.get():
                    self.project_name_entry.delete(0, "end")
                    self.project_name_entry.insert(0, c.site_location)
                break

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
            cust_names = [f"{c.name} ({c.mobile_number})" for c in self.customers_cache]
            self.customer_combo.configure(values=cust_names)
            selected_str = f"{new_c.name} ({new_c.mobile_number})"
            self.customer_combo.set(selected_str)
            self.on_customer_selected(selected_str)
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="Save Customer",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=save_quick_cust
        ).pack(pady=(0, 20))

    def recalculate_totals(self):
        gross = 0.0
        for aw in self.area_widgets:
            adata = aw.get_data()
            for it in adata["items"]:
                gross += it["total_amount"]

        try:
            round_off = float(self.round_off_entry.get().strip() or 0.0)
        except ValueError:
            round_off = 0.0

        net = round(gross + round_off, 2)
        self.gross_total_lbl.configure(text=f"₹ {gross:,.2f}")
        self.net_total_lbl.configure(text=f"₹ {net:,.2f}")

    def collect_quotation_payload(self):
        # Validate customer
        selected_cust_str = self.customer_combo.get()
        matched_cust = None
        for c in self.customers_cache:
            if f"{c.name} ({c.mobile_number})" == selected_cust_str:
                matched_cust = c
                break
        if not matched_cust:
            raise ValueError("Please select a valid customer.")

        # Validate salesperson
        selected_sp_str = self.salesperson_combo.get()
        matched_sp = None
        for s in self.salespersons_cache:
            if f"{s.name} ({s.role})" == selected_sp_str:
                matched_sp = s
                break
        if not matched_sp:
            raise ValueError("Please select a sales associate.")

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
            raise ValueError("Quotation must contain at least one item description.")

        return {
            "id": self.quote_id,
            "quotation_number": self.quote_num_entry.get().strip(),
            "quotation_date": self.date_entry.get().strip() or date.today(),
            "customer_id": matched_cust.id,
            "sales_person_id": matched_sp.id,
            "project_name": self.project_name_entry.get().strip(),
            "special_notes": self.notes_entry.get("1.0", "end").strip(),
            "status": self.status_combo.get(),
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
