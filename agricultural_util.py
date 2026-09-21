import json
import os
import re
from typing import List

import streamlit as st
from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, field_validator

load_dotenv()


def get_secret(name: str, default=None):
    """Read a secret from Streamlit Cloud first, then local .env."""
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


class CropRecommendation(BaseModel):
    crop_name: str = Field(description="Recommended crop name")
    planting_season: str = Field(description="Best planting season")
    care_instructions: List[str] = Field(description="Care and maintenance tips")
    expected_yield: str = Field(description="Expected yield information")
    market_value: str = Field(description="Current market value/demand")

    @field_validator("crop_name", mode="before")
    @classmethod
    def clean_crop_name(cls, value):
        if isinstance(value, dict):
            return value.get("description", str(value))
        return str(value)


class DiseaseAnalysis(BaseModel):
    disease_name: str = Field(description="Identified disease name")
    severity: str = Field(description="Disease severity level")
    symptoms: List[str] = Field(description="Key symptoms identified")
    treatment: List[str] = Field(description="Treatment recommendations")
    prevention: List[str] = Field(description="Prevention measures")


class SoilAnalysis(BaseModel):
    soil_type: str = Field(description="Soil type classification")
    ph_level: str = Field(description="Soil pH analysis")
    nutrient_status: List[str] = Field(description="Nutrient deficiencies/excesses")
    recommendations: List[str] = Field(description="Soil improvement suggestions")
    suitable_crops: List[str] = Field(description="Crops suitable for this soil")


class WeatherAdvisory(BaseModel):
    current_conditions: str = Field(description="Current weather summary")
    farming_impact: str = Field(description="Impact on farming activities")
    recommendations: List[str] = Field(description="Weather-based farming advice")
    alerts: List[str] = Field(description="Important weather alerts")


class MarketAnalysis(BaseModel):
    crop_name: str = Field(description="Crop being analyzed")
    current_price: str = Field(description="Current market price")
    price_trend: str = Field(description="Price trend analysis")
    demand_status: str = Field(description="Market demand status")
    selling_tips: List[str] = Field(description="Tips for better selling")


class GreenCureAI:
    KEY_NAMES = {
        "GROQ1": "GROQ_API_KEY_1",
        "GROQ2": "GROQ_API_KEY_2",
        "GROQ3": "GROQ_API_KEY_3",
        "GROQ4": "GROQ_API_KEY_4",
    }

    def __init__(self, api_key_name="GROQ1"):
        if api_key_name not in self.KEY_NAMES:
            raise ValueError(f"Unknown AI key selection: {api_key_name}")

        env_name = self.KEY_NAMES[api_key_name]
        api_key = get_secret(env_name)
        if not api_key:
            raise ValueError(f"Missing Streamlit Secret/environment variable: {env_name}")

        self.api_key_name = api_key_name
        self.llm = ChatGroq(
            api_key=api_key,
            model="openai/gpt-oss-20b",
            temperature=0.7,
        )

    @staticmethod
    def available_keys():
        return [name for name, env_name in GreenCureAI.KEY_NAMES.items() if get_secret(env_name)]

    @staticmethod
    def _clean_response(content: str) -> str:
        content = content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)
        return content.strip()

    def _invoke_structured(self, prompt: PromptTemplate, parser: PydanticOutputParser, **values):
        last_error = None
        for _ in range(3):
            try:
                response = self.llm.invoke(prompt.format(**values))
                content = self._clean_response(response.content)
                return parser.parse(content)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"AI response could not be parsed: {last_error}")

    def get_crop_recommendation(self, location, soil_type, season, farm_size):
        parser = PydanticOutputParser(pydantic_object=CropRecommendation)
        prompt = PromptTemplate(
            template=(
                "As an agricultural expert specializing in Indian farming, provide ONE SINGLE crop recommendation.\n"
                "Location: {location}\nSoil Type: {soil_type}\nSeason: {season}\nFarm Size: {farm_size}\n\n"
                "Consider Indian agricultural conditions, monsoon patterns and local market demand.\n"
                "Return exactly one recommendation and follow these formatting instructions:\n"
                "{format_instructions}"
            ),
            input_variables=["location", "soil_type", "season", "farm_size"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        try:
            result = self._invoke_structured(
                prompt,
                parser,
                location=location,
                soil_type=soil_type,
                season=season,
                farm_size=farm_size,
            )
            if result.crop_name and result.care_instructions:
                return result
        except Exception:
            pass

        return CropRecommendation(
            crop_name="Wheat",
            planting_season="Rabi season (November-December)",
            care_instructions=[
                "Prepare and level the field properly.",
                "Apply suitable organic manure and nutrients based on soil testing.",
                "Maintain an appropriate irrigation schedule and monitor pests.",
            ],
            expected_yield="25-30 quintals per hectare",
            market_value="Market price varies by region and season; check your local mandi.",
        )

    def diagnose_crop_disease(self, crop_type, symptoms, region):
        parser = PydanticOutputParser(pydantic_object=DiseaseAnalysis)
        prompt = PromptTemplate(
            template=(
                "As a plant pathology expert familiar with Indian crop diseases, analyze:\n"
                "Crop: {crop_type}\nSymptoms: {symptoms}\nRegion: {region}\n\n"
                "Give a cautious, likely diagnosis and practical treatment/prevention advice.\n"
                "Return JSON following:\n{format_instructions}"
            ),
            input_variables=["crop_type", "symptoms", "region"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return self._invoke_structured(parser=parser, prompt=prompt, crop_type=crop_type, symptoms=symptoms, region=region)

    def analyze_soil_conditions(self, ph_level, organic_matter, drainage, region):
        parser = PydanticOutputParser(pydantic_object=SoilAnalysis)
        prompt = PromptTemplate(
            template=(
                "As a soil scientist specializing in Indian agriculture, analyze:\n"
                "pH: {ph_level}\nOrganic Matter: {organic_matter}\nDrainage: {drainage}\nRegion: {region}\n\n"
                "Return JSON following:\n{format_instructions}"
            ),
            input_variables=["ph_level", "organic_matter", "drainage", "region"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return self._invoke_structured(parser=parser, prompt=prompt, ph_level=ph_level, organic_matter=organic_matter, drainage=drainage, region=region)

    def get_weather_advisory(self, location, current_weather, crop_stage):
        parser = PydanticOutputParser(pydantic_object=WeatherAdvisory)
        prompt = PromptTemplate(
            template=(
                "As a meteorological agriculture advisor for Indian farming, provide weather-based guidance:\n"
                "Location: {location}\nCurrent Weather: {current_weather}\nCrop Stage: {crop_stage}\n\n"
                "Consider Indian monsoon patterns and regional weather impacts.\n"
                "Return JSON following:\n{format_instructions}"
            ),
            input_variables=["location", "current_weather", "crop_stage"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return self._invoke_structured(parser=parser, prompt=prompt, location=location, current_weather=current_weather, crop_stage=crop_stage)

    def analyze_market_conditions(self, crop_name, location, quantity):
        parser = PydanticOutputParser(pydantic_object=MarketAnalysis)
        prompt = PromptTemplate(
            template=(
                "As an Indian agricultural market analyst, analyze:\n"
                "Crop: {crop_name}\nLocation: {location}\nQuantity: {quantity}\n\n"
                "Do not claim guaranteed or live prices. Clearly frame prices as estimates when appropriate.\n"
                "Return JSON following:\n{format_instructions}"
            ),
            input_variables=["crop_name", "location", "quantity"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return self._invoke_structured(parser=parser, prompt=prompt, crop_name=crop_name, location=location, quantity=quantity)
