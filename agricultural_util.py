import os
from typing import List, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator
import requests
from datetime import datetime

load_dotenv()

class CropRecommendation(BaseModel):
    crop_name: str = Field(description="Recommended crop name")
    planting_season: str = Field(description="Best planting season")
    care_instructions: List[str] = Field(description="Care and maintenance tips")
    expected_yield: str = Field(description="Expected yield information")
    market_value: str = Field(description="Current market value/demand")
    
    @field_validator('crop_name', mode="before")
    def clean_crop_name(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class DiseaseAnalysis(BaseModel):
    disease_name: str = Field(description="Identified disease name")
    severity: str = Field(description="Disease severity level")
    symptoms: List[str] = Field(description="Key symptoms identified")
    treatment: List[str] = Field(description="Treatment recommendations")
    prevention: List[str] = Field(description="Prevention measures")
    
    @field_validator('disease_name', mode="before")
    def clean_disease_name(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class SoilAnalysis(BaseModel):
    soil_type: str = Field(description="Soil type classification")
    ph_level: str = Field(description="Soil pH analysis")
    nutrient_status: List[str] = Field(description="Nutrient deficiencies/excesses")
    recommendations: List[str] = Field(description="Soil improvement suggestions")
    suitable_crops: List[str] = Field(description="Crops suitable for this soil")
    
    @field_validator('soil_type', mode="before")
    def clean_soil_type(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class WeatherAdvisory(BaseModel):
    current_conditions: str = Field(description="Current weather summary")
    farming_impact: str = Field(description="Impact on farming activities")
    recommendations: List[str] = Field(description="Weather-based farming advice")
    alerts: List[str] = Field(description="Important weather alerts")
    
    @field_validator('current_conditions', mode="before")
    def clean_conditions(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class MarketAnalysis(BaseModel):
    crop_name: str = Field(description="Crop being analyzed")
    current_price: str = Field(description="Current market price")
    price_trend: str = Field(description="Price trend analysis")
    demand_status: str = Field(description="Market demand status")
    selling_tips: List[str] = Field(description="Tips for better selling")
    
    @field_validator('crop_name', mode="before")
    def clean_crop_name(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class GreenCureAI:
    def __init__(self, api_key_name=None):
        api_key_mapping = {
    "GROQ1": "GROQ_API_KEY_1",
    "GROQ2": "GROQ_API_KEY_2",
    "GROQ3": "GROQ_API_KEY_3",
    "GROQ4": "GROQ_API_KEY_4"
    }
        
        api_key_value = None
        if api_key_name and api_key_name in api_key_mapping:
            env_var_name = api_key_mapping[api_key_name]
            api_key_value = os.getenv(env_var_name)
        
        if not api_key_value:
            raise ValueError(f"API key not found for {api_key_name}")
            
        self.llm = ChatGroq(
            api_key=api_key_value,
            model="llama-3.1-8b-instant",
            temperature=0.7
        )

    def get_crop_recommendation(self, location: str, soil_type: str, 
                           season: str, farm_size: str) -> CropRecommendation:
        """Generate crop recommendations based on location and conditions"""
        parser = PydanticOutputParser(pydantic_object=CropRecommendation)
        
        prompt = PromptTemplate(
            template=(
                "As an agricultural expert specializing in Indian farming, provide ONE SINGLE crop recommendation for:\n"
                "Location: {location}\n"
                "Soil Type: {soil_type}\n" 
                "Season: {season}\n"
                "Farm Size: {farm_size}\n\n"
                "Consider Indian agricultural conditions, monsoon patterns, and local market demands.\n"
                "Return ONLY ONE crop recommendation in this EXACT JSON format:\n\n"
                "{{\n"
                '  "crop_name": "Name of the SINGLE most suitable crop",\n'
                '  "planting_season": "Best time to plant this crop with specific months",\n'
                '  "care_instructions": ["Detailed instruction 1", "Detailed instruction 2", "Detailed instruction 3"],\n'
                '  "expected_yield": "Realistic yield per acre as a simple string",\n'
                '  "market_value": "Current market price and demand as a simple string"\n'
                "}}\n\n"
                "IMPORTANT: Return only ONE crop, not a list. Market value should be a simple string, not an object.\n"
                "Focus on the MOST suitable crop for the given conditions.\n"
                "{format_instructions}"
            ),
            input_variables=["location", "soil_type", "season", "farm_size"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.llm.invoke(prompt.format(
                    location=location, soil_type=soil_type, 
                    season=season, farm_size=farm_size
                ))
                
                content = response.content.strip()
                
                if content.startswith('['):
                    import json
                    try:
                        json_array = json.loads(content)
                        if isinstance(json_array, list) and len(json_array) > 0:
                            first_recommendation = json_array[0]
                            
                            if isinstance(first_recommendation.get('market_value'), dict):
                                market_info = first_recommendation['market_value']
                                price = market_info.get('current_price', 'Price varies')
                                demand = market_info.get('demand', 'Good demand')
                                first_recommendation['market_value'] = f"{price}, {demand}"
                            
                            content = json.dumps(first_recommendation)
                    except json.JSONDecodeError:
                        pass
                
                parsed_result = parser.parse(content)
                
                if not parsed_result.crop_name or not parsed_result.care_instructions:
                    raise ValueError("Invalid crop recommendation format")
                
                return parsed_result
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    return CropRecommendation(
                        crop_name="Wheat",
                        planting_season="Rabi season (November-December) for your region",
                        care_instructions=[
                            "Prepare field with proper ploughing and leveling",
                            "Apply organic manure 15-20 tons per hectare",
                            "Maintain proper irrigation schedule"
                        ],
                        expected_yield="25-30 quintals per hectare",
                        market_value="₹2000-2500 per quintal with good market demand"
                    )
                continue


    def diagnose_crop_disease(self, crop_type: str, symptoms: str, 
                             region: str) -> DiseaseAnalysis:
        """Diagnose crop diseases based on symptoms"""
        parser = PydanticOutputParser(pydantic_object=DiseaseAnalysis)
        
        prompt = PromptTemplate(
            template=(
                "As a plant pathology expert familiar with Indian crop diseases, analyze this case:\n"
                "Crop: {crop_type}\n"
                "Symptoms: {symptoms}\n"
                "Region: {region}\n\n"
                "Provide detailed analysis in JSON format:\n"
                '{{\n'
                '  "disease_name": "Most likely disease based on symptoms",\n'
                '  "severity": "Low/Medium/High",\n'
                '  "symptoms": ["Key symptom 1", "Key symptom 2", "Key symptom 3"],\n'
                '  "treatment": ["Treatment step 1", "Treatment step 2", "Treatment step 3"],\n'
                '  "prevention": ["Prevention measure 1", "Prevention measure 2", "Prevention measure 3"]\n'
                '}}\n\n'
                "Focus on treatments available in Indian agricultural context.\n"
                "Your response:"
            ),
            input_variables=["crop_type", "symptoms", "region"]
        )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.llm.invoke(prompt.format(
                    crop_type=crop_type, symptoms=symptoms, region=region
                ))
                
                parsed_result = parser.parse(response.content)
                
                if not parsed_result.disease_name or not parsed_result.treatment:
                    raise ValueError("Invalid disease analysis format")
                
                return parsed_result
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Failed to generate disease diagnosis after {max_attempts} attempts: {str(e)}")
                continue

    def analyze_soil_conditions(self, ph_level: float, organic_matter: str, 
                               drainage: str, region: str) -> SoilAnalysis:
        """Analyze soil conditions and provide recommendations"""
        parser = PydanticOutputParser(pydantic_object=SoilAnalysis)
        
        prompt = PromptTemplate(
            template=(
                "As a soil scientist expert in Indian agricultural conditions, analyze these soil parameters:\n"
                "pH Level: {ph_level}\n"
                "Organic Matter: {organic_matter}\n"
                "Drainage: {drainage}\n"
                "Region: {region}\n\n"
                "Provide comprehensive soil analysis in JSON format:\n"
                '{{\n'
                '  "soil_type": "Soil classification based on given parameters",\n'
                '  "ph_level": "Analysis of pH level and its implications",\n'
                '  "nutrient_status": ["Nutrient analysis 1", "Nutrient analysis 2", "Nutrient analysis 3"],\n'
                '  "recommendations": ["Improvement suggestion 1", "Improvement suggestion 2", "Improvement suggestion 3"],\n'
                '  "suitable_crops": ["Crop 1", "Crop 2", "Crop 3", "Crop 4"]\n'
                '}}\n\n'
                "Consider Indian soil types and regional agricultural practices.\n"
                "Your response:"
            ),
            input_variables=["ph_level", "organic_matter", "drainage", "region"]
        )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.llm.invoke(prompt.format(
                    ph_level=ph_level, organic_matter=organic_matter,
                    drainage=drainage, region=region
                ))
                
                parsed_result = parser.parse(response.content)
                
                if not parsed_result.soil_type or not parsed_result.recommendations:
                    raise ValueError("Invalid soil analysis format")
                
                return parsed_result
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Failed to generate soil analysis after {max_attempts} attempts: {str(e)}")
                continue

    def get_weather_advisory(self, location: str, current_weather: str, 
                           crop_stage: str) -> WeatherAdvisory:
        """Provide weather-based farming advisory"""
        parser = PydanticOutputParser(pydantic_object=WeatherAdvisory)
        
        prompt = PromptTemplate(
            template=(
                "As a meteorological agriculture advisor for Indian farming, provide weather-based guidance:\n"
                "Location: {location}\n"
                "Current Weather: {current_weather}\n"
                "Crop Stage: {crop_stage}\n\n"
                "Provide weather advisory in JSON format:\n"
                '{{\n'
                '  "current_conditions": "Summary of current weather conditions",\n'
                '  "farming_impact": "How current weather affects farming activities",\n'
                '  "recommendations": ["Weather-based advice 1", "Weather-based advice 2", "Weather-based advice 3"],\n'
                '  "alerts": ["Important alert 1", "Important alert 2"]\n'
                '}}\n\n'
                "Consider Indian monsoon patterns and regional weather impacts.\n"
                "Your response:"
            ),
            input_variables=["location", "current_weather", "crop_stage"]
        )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.llm.invoke(prompt.format(
                    location=location, current_weather=current_weather,
                    crop_stage=crop_stage
                ))
                
                parsed_result = parser.parse(response.content)
                
                if not parsed_result.current_conditions or not parsed_result.recommendations:
                    raise ValueError("Invalid weather advisory format")
                
                return parsed_result
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Failed to generate weather advisory after {max_attempts} attempts: {str(e)}")
                continue

    def analyze_market_conditions(self, crop_name: str, location: str, 
                                 quantity: str) -> MarketAnalysis:
        """Analyze market conditions for crops"""
        parser = PydanticOutputParser(pydantic_object=MarketAnalysis)
        
        prompt = PromptTemplate(
            template=(
                "As a market analyst specializing in Indian agricultural markets, analyze:\n"
                "Crop: {crop_name}\n"
                "Location: {location}\n"
                "Quantity: {quantity}\n\n"
                "Provide market analysis in JSON format:\n"
                '{{\n'
                '  "crop_name": "Crop being analyzed",\n'
                '  "current_price": "Current market price range in Indian context",\n'
                '  "price_trend": "Price trend analysis and future predictions",\n'
                '  "demand_status": "Current market demand status",\n'
                '  "selling_tips": ["Best time to sell (season/month)", "Where to sell (mandi/export/local)", "Pricing strategy"]\n'
                '}}\n\n'
                "Consider Indian mandi prices and regional market variations.\n"
                "Your response:"
            ),
            input_variables=["crop_name", "location", "quantity"]
        )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.llm.invoke(prompt.format(
                    crop_name=crop_name, location=location, quantity=quantity
                ))
                
                parsed_result = parser.parse(response.content)
                
                # Validate the response
                if not parsed_result.crop_name or not parsed_result.selling_tips:
                    raise ValueError("Invalid market analysis format")
                
                return parsed_result
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Failed to generate market analysis after {max_attempts} attempts: {str(e)}")
                continue
