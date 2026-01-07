from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import uuid4, UUID
import uvicorn

app = FastAPI(title="Advertisement Service", version="1.0.0")

class Advertisement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    price: float = Field(..., gt=0)
    author: str = Field(..., min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class AdvertisementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    price: float = Field(..., gt=0)
    author: str = Field(..., min_length=1, max_length=100)


class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    author: Optional[str] = Field(None, min_length=1, max_length=100)

advertisements_db = {}

@app.post("/advertisement", response_model=Advertisement, status_code=201)
def create_advertisement(ad: AdvertisementCreate):
    advertisement = Advertisement(**ad.dict())
    advertisements_db[str(advertisement.id)] = advertisement
    return advertisement

@app.patch("/advertisement/{advertisement_id}", response_model=Advertisement)
def update_advertisement(advertisement_id: str, ad_update: AdvertisementUpdate):
    if advertisement_id not in advertisements_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    advertisement = advertisements_db[advertisement_id]
    update_data = ad_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(advertisement, field, value)

    advertisements_db[advertisement_id] = advertisement
    return advertisement

@app.delete("/advertisement/{advertisement_id}", status_code=204)
def delete_advertisement(advertisement_id: str):
    if advertisement_id not in advertisements_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    del advertisements_db[advertisement_id]
    return None

@app.get("/advertisement/{advertisement_id}", response_model=Advertisement)
def get_advertisement(advertisement_id: str):
    if advertisement_id not in advertisements_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return advertisements_db[advertisement_id]

@app.get("/advertisement", response_model=List[Advertisement])
def search_advertisements(
        title: Optional[str] = Query(None, min_length=1),
        description: Optional[str] = Query(None, min_length=1),
        author: Optional[str] = Query(None, min_length=1),
        price_min: Optional[float] = Query(None, gt=0),
        price_max: Optional[float] = Query(None, gt=0),
        created_after: Optional[datetime] = Query(None),
        created_before: Optional[datetime] = Query(None)
):

    if price_min and price_max and price_min > price_max:
        raise HTTPException(
            status_code=400,
            detail="price_min cannot be greater than price_max"
        )

    results = []
    for ad in advertisements_db.values():
        if title and title.lower() not in ad.title.lower():
            continue

        if description and description.lower() not in ad.description.lower():
            continue

        if author and author.lower() not in ad.author.lower():
            continue

        if price_min and ad.price < price_min:
            continue

        if price_max and ad.price > price_max:
            continue

        if created_after and ad.created_at < created_after:
            continue

        if created_before and ad.created_at > created_before:
            continue

        results.append(ad)

    return results

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)