from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from API.dependencies import get_session, require_permission
from API.schemas import (
    CategoryCreate,
    ConfigurationCreate,
    PriceUpdate,
    ProductCreate,
)
from authentication.models.user import CATALOG_READ, CATALOG_WRITE
from catalog.models.brand import Brand
from catalog.models.product import Product
from catalog.models.product_configuration import ProductConfiguration
from catalog.models.specification import Specification, SpecificationValueType
from catalog.repositories.category_repository import CategoryRepository
from catalog.repositories.configuration_repository import ConfigurationRepository
from catalog.repositories.pricing_repository import PricingRepository
from catalog.repositories.product_repository import ProductRepository
from catalog.services.category_service import CategoryService
from catalog.services.specification_service import SpecificationService
from shared.pricing import Pricing, PricingRule

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.post("/categories", status_code=201)
def create_category(
    payload: CategoryCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(CATALOG_WRITE)),
):
    service = CategoryService(
        CategoryRepository(session),
        SpecificationService(None),
    )
    service.create_category(
        payload.name,
        {
            item.name: {
                "spec_type_name": item.name,
                "spec_type_value_type": SpecificationValueType(item.value_type),
                "allowed_values": item.allowed_values,
            }
            for item in payload.specification_types
        },
        payload.description,
    )
    return {"name": payload.name, "created": True}


@router.post("/products", status_code=201)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(CATALOG_WRITE)),
):
    _, category = CategoryRepository(session).category_exists(payload.category_name)
    if category is None:
        raise HTTPException(404, f"Category '{payload.category_name}' was not found.")

    product = Product(
        product_id=payload.product_id,
        name=payload.name,
        description=payload.description,
        brand=Brand(name=payload.brand_name, products=[payload.product_id]),
        category=category,
        configurations=[],
    )
    ProductRepository(session).add_product(product)
    return {"product_id": product.product_id, "created": True}


@router.post("/configurations", status_code=201)
def create_configuration(
    payload: ConfigurationCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(CATALOG_WRITE)),
):
    product = ProductRepository(session).get_product(payload.product_id)
    if product is None:
        raise HTTPException(404, f"Product '{payload.product_id}' was not found.")

    allowed_types = {
        specification_type.name: specification_type
        for specification_type in product.category.specification_types
    }
    specifications = []
    for name, value in payload.specifications.items():
        specification_type = allowed_types.get(name)
        if specification_type is None:
            raise HTTPException(
                400,
                f"Specification '{name}' is not required by category "
                f"'{product.category.name}'.",
            )
        specifications.append(Specification(type=specification_type, value=value))

    configuration = ProductConfiguration(
        product=product,
        specifications=specifications,
        pricing=Pricing(
            pricing_rules=[
                PricingRule(
                    min_quantity=rule.min_quantity,
                    max_quantity=rule.max_quantity,
                    unit_price=rule.unit_price,
                )
                for rule in payload.pricing_rules
            ]
        ),
        material=payload.material,
        weight=payload.weight,
        color=payload.color,
        size=payload.size,
        volume=payload.volume,
        length=payload.length,
        width=payload.width,
        unit=payload.unit,
        additional_features=payload.additional_features,
    )
    configuration_id = ConfigurationRepository(session).save_configuration(configuration)
    return {"configuration_id": configuration_id}


@router.get("/products/{product_id}")
def get_product(
    product_id: str,
    session: Session = Depends(get_session),
    _=Depends(require_permission(CATALOG_READ)),
):
    product = ProductRepository(session).get_product(product_id)
    if product is None:
        raise HTTPException(404, f"Product '{product_id}' was not found.")
    return {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "brand": product.brand.name,
        "category": product.category.name,
        "configuration_count": len(product.configurations),
    }


@router.put("/prices/{product_name}")
def set_price(
    product_name: str,
    payload: PriceUpdate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(CATALOG_WRITE)),
):
    PricingRepository(session).save_price(product_name, payload.unit_price)
    return {"product_name": product_name, "unit_price": payload.unit_price}
