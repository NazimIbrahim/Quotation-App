"""
Brands & Sizes Catalog API Router:
Handles listing and management of Tile Brands, Packaging Sizes,
and Multi-Unit Product Types (Box, Sqft, Pieces, Bags, Nos).
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.models import TileBrand, BrandSizeCoverage

router = APIRouter()


class BrandCreatePayload(BaseModel):
    name: str
    description: Optional[str] = None


class SizeCreatePayload(BaseModel):
    size: str
    product_type: str = "Box"
    coverage_sqft: float = 15.5
    pieces_per_box: int = 2
    default_rate_sqft: float = 0.0
    default_rate_box: float = 0.0


@router.get("")
def list_brands():
    """Lists all brands and their configured sizes, coverage areas, product types, and default rates."""
    brands = TileBrand.select().where(TileBrand.is_active == True).order_by(TileBrand.name)
    results = []

    for b in brands:
        sizes_data = []
        for s in b.size_coverages.order_by(BrandSizeCoverage.size):
            sizes_data.append({
                "id": s.id,
                "size": s.size,
                "product_type": getattr(s, "product_type", "Box") or "Box",
                "coverage_sqft": float(s.coverage_sqft or 0.0),
                "pieces_per_box": int(s.pieces_per_box or 1),
                "default_rate_sqft": float(s.default_rate_sqft or 0.0),
                "default_rate_box": float(s.default_rate_box or 0.0),
            })

        results.append({
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "sizes_count": len(sizes_data),
            "sizes": sizes_data
        })

    return {"count": len(results), "brands": results}


@router.post("")
def create_brand(payload: BrandCreatePayload):
    """Creates a new tile brand."""
    try:
        brand = TileBrand.create(
            name=payload.name.strip(),
            description=payload.description.strip() if payload.description else None
        )
        return {"success": True, "id": brand.id, "name": brand.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create brand: {str(e)}")


@router.post("/{brand_id}/sizes")
def add_size_to_brand(brand_id: int, payload: SizeCreatePayload):
    """Adds a packaging size and product type to a brand."""
    brand = TileBrand.get_or_none(TileBrand.id == brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    try:
        sc = BrandSizeCoverage.create(
            brand=brand,
            size=payload.size.strip(),
            product_type=payload.product_type.strip(),
            coverage_sqft=payload.coverage_sqft,
            pieces_per_box=payload.pieces_per_box,
            default_rate_sqft=payload.default_rate_sqft,
            default_rate_box=payload.default_rate_box,
        )
        return {
            "success": True,
            "id": sc.id,
            "size": sc.size,
            "product_type": sc.product_type,
            "coverage_sqft": sc.coverage_sqft
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add size: {str(e)}")
