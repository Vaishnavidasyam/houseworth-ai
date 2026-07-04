# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr
import joblib
import os

from data_preprocessing import HyderabadHousePreprocessor
from bengaluru_preprocessing import BengaluruHousePreprocessor
from mumbai_preprocessing import MumbaiHousePreprocessor
from kolkata_preprocessing import KolkataHousePreprocessor
from gurgaon_preprocessing import GurgaonHousePreprocessor


app = FastAPI(title="Multi-City House Price API")

# Allow React frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://houseworth-ai.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic models ----------

class PriceInput(BaseModel):
    city: constr(strip_whitespace=True)
    place: constr(strip_whitespace=True)  # locality
    bhk: int
    area_sqm: float


class PriceOutput(BaseModel):
    city: str
    bhk: int
    place: str
    area_sqm: float
    price_per_sqm: float
    total_price: float


# ---------- Startup: load all city models ----------

@app.on_event("startup")
def startup_event():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")

    app.state.city_preprocessors = {}
    app.state.city_bhk_models = {}

    def load_city(
        city_name: str,
        model_subdir: str,
        uses_hyd_naming: bool = False,
    ):
        """
        Load preprocessor + 2BHK/3BHK models for a city.
        Hyderabad uses models/rf_2bhk.pkl etc. directly.
        Others use models/<city_subdir>/rf_*.pkl
        """
        print(f"Loading models for {city_name}...")

        # Preprocessor path
        if uses_hyd_naming:
            preproc_path = os.path.join(models_dir, "preprocessor.pkl")
        else:
            preproc_path = os.path.join(models_dir, model_subdir, "preprocessor.pkl")

        if not os.path.exists(preproc_path):
            print(f"[WARN] Preprocessor missing for {city_name}: {preproc_path}")
            return

        preprocessor = joblib.load(preproc_path)

        # Model paths
        if uses_hyd_naming:
            model_2_path = os.path.join(models_dir, "rf_2bhk.pkl")
            model_3_path = os.path.join(models_dir, "rf_3bhk.pkl")
        else:
            city_model_dir = os.path.join(models_dir, model_subdir)
            model_2_path = os.path.join(city_model_dir, "rf_2bhk.pkl")
            model_3_path = os.path.join(city_model_dir, "rf_3bhk.pkl")

        models_for_city = {}
        if os.path.exists(model_2_path):
            models_for_city[2] = joblib.load(model_2_path)
        if os.path.exists(model_3_path):
            models_for_city[3] = joblib.load(model_3_path)

        if not models_for_city:
            print(f"[WARN] No BHK models found for {city_name}")
            return

        app.state.city_preprocessors[city_name] = preprocessor
        app.state.city_bhk_models[city_name] = models_for_city
        print(f"[OK] Loaded {city_name}: {list(models_for_city.keys())} BHK models")

    # Hyderabad (old naming – models/ directly)
    load_city("Hyderabad", model_subdir=".", uses_hyd_naming=True)

    # Bengaluru
    load_city("Bengaluru", model_subdir="bengaluru")

    # Mumbai
    load_city("Mumbai", model_subdir="mumbai")

    # Kolkata
    load_city("Kolkata", model_subdir="kolkata")

    # Gurgaon
    load_city("Gurgaon", model_subdir="gurgaon")

    print("Available cities:", list(app.state.city_preprocessors.keys()))


# ---------- Prediction endpoint ----------

@app.post("/predict", response_model=PriceOutput)
def predict_price(inp: PriceInput):
    city = inp.city.strip()

    if inp.bhk not in [2, 3]:
        raise HTTPException(status_code=400, detail="Only 2BHK and 3BHK are supported.")

    if inp.area_sqm <= 0:
        raise HTTPException(status_code=400, detail="area_sqm must be > 0.")

    if city not in app.state.city_preprocessors:
        raise HTTPException(
            status_code=400,
            detail=f"No model available for city: {city}",
        )

    city_models = app.state.city_bhk_models.get(city, {})
    model = city_models.get(inp.bhk)
    if model is None:
        raise HTTPException(
            status_code=400,
            detail=f"No model available for {inp.bhk}BHK in {city}",
        )

    preprocessor = app.state.city_preprocessors[city]

    # Encode locality for this city
    try:
        locality_enc = preprocessor.encode_locality(inp.place)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Locality '{inp.place}' not seen during training for {city}.",
        ) from e

    X_input = [[locality_enc, inp.area_sqm]]

    price_per_sqm = float(model.predict(X_input)[0])
    total_price = price_per_sqm * inp.area_sqm

    return PriceOutput(
        city=city,
        bhk=inp.bhk,
        place=inp.place,
        area_sqm=inp.area_sqm,
        price_per_sqm=round(price_per_sqm, 2),
        total_price=round(total_price, 2),
    )


@app.get("/")
def root():
    return {
        "message": "Multi-City House Price Prediction API",
        "cities": list(app.state.city_preprocessors.keys()) if hasattr(app.state, "city_preprocessors") else [],
        "endpoint": "/predict",
        "sample_json": {
            "city": "Hyderabad",
            "place": "Gachibowli",
            "bhk": 3,
            "area_sqm": 120,
        },
    }
