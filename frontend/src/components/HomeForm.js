import React, { useState, useEffect } from "react";
import axios from "axios";
import "./HomeForm.css";

const CITY_LOCALITIES = {
  Hyderabad: [
    "Nanakramguda",
    "Gachibowli",
    "Kondapur",
    "Madhapur",
    "Kukatpally",
    "Banjara Hills",
    "Jubilee Hills",
  ],

  Bengaluru: [
    "Electronic City",
    "Whitefield",
    "Koramangala",
    "HSR Layout",
    "Indiranagar",
  ],

  Mumbai: ["Andheri", "Bandra", "Powai", "Borivali"],

  Kolkata: ["Salt Lake", "New Town", "Behala", "Rajarhat"],

  Gurgaon: ["DLF Phase 1", "Golf Course Road", "MG Road"],
};

const CITIES = Object.keys(CITY_LOCALITIES);

const AREA_PRESETS = [70, 90, 110, 130];

const HomeForm = ({ onResult, onFormChange, initialValues }) => {
  const [city, setCity] = useState(initialValues?.city || "");

  const [place, setPlace] = useState(initialValues?.place || "");

  const [bhk, setBhk] = useState(initialValues?.bhk || null);

  const [areaSqM, setAreaSqM] = useState(initialValues?.areaSqM || "");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const localitiesForCity = CITY_LOCALITIES[city] || [];

  useEffect(() => {
    onFormChange &&
      onFormChange({
        city,
        place,
        bhk,
        areaSqM,
      });
  }, [city, place, bhk, areaSqM, onFormChange]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    if (!city) {
      setError("Please select a city.");
      return;
    }

    if (!place) {
      setError("Please select a locality.");
      return;
    }

    if (!bhk) {
      setError("Please select BHK.");
      return;
    }

    if (!areaSqM) {
      setError("Please enter area.");
      return;
    }

    setLoading(true);

    try {
      const API_URL = process.env.REACT_APP_API_URL || "/api";
      const res = await axios.post(`${API_URL}/predict`, {
        city,
        place,
        bhk: Number(bhk),
        area_sqm: Number(areaSqM),
      });

      onResult && onResult(res.data);
    } catch (err) {
      setError("Backend connection failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="hf-form" onSubmit={handleSubmit}>
      {/* CITY */}

      <div className="hf-field">
        <label className="hf-label">City</label>

        <select
          className="hf-input"
          value={city}
          onChange={(e) => {
            setCity(e.target.value);
            setPlace("");
          }}
        >
          <option value="">Select City</option>

          {CITIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* LOCALITY */}

      <div className="hf-field">
        <label className="hf-label">Locality</label>

        <select
          className="hf-input"
          value={place}
          onChange={(e) => setPlace(e.target.value)}
        >
          <option value="">Select Locality</option>

          {localitiesForCity.map((loc) => (
            <option key={loc} value={loc}>
              {loc}
            </option>
          ))}
        </select>
      </div>

      {/* BHK */}

      <div className="hf-field">
        <label className="hf-label">BHK Type</label>

        <div className="hf-bhk-toggle">
          {[2, 3].map((val) => (
            <button
              key={val}
              type="button"
              className={`hf-bhk-chip ${bhk === val ? "active" : ""}`}
              onClick={() => setBhk(val)}
            >
              {val} BHK
            </button>
          ))}
        </div>
      </div>

      {/* AREA */}

      <div className="hf-field">
        <label className="hf-label">Area (sq m)</label>

        <input
          type="number"
          className="hf-input"
          value={areaSqM}
          onChange={(e) => setAreaSqM(e.target.value)}
          placeholder="Enter area"
        />

        <div className="hf-presets">
          {AREA_PRESETS.map((val) => (
            <button
              type="button"
              key={val}
              className={`hf-preset-chip ${
                Number(areaSqM) === val ? "active" : ""
              }`}
              onClick={() => setAreaSqM(val)}
            >
              {val} m²
            </button>
          ))}
        </div>
      </div>

      {error && <div className="hf-error">{error}</div>}

      <button type="submit" className="hf-submit">
        {loading ? "Predicting..." : "Predict Price"}
      </button>
    </form>
  );
};

export default HomeForm;
