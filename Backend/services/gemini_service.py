import json
from typing import Dict, Any
from fastapi import HTTPException
from google import genai
from google.genai.types import GenerateContentConfig, Tool, GoogleSearch
from config.settings import settings

# Initialize Google Gen AI client with Vertex AI
client = genai.Client(
    vertexai=True,
    project=settings.GCP_PROJECT_ID,
    location=settings.GCP_LOCATION
)

async def analyze_with_gemini(extracted_text: str, weightage: Dict[str, int]) -> Dict[str, Any]:
    """Analyze pitch deck content using Gemini 2.5 Pro with Google Search grounding"""
    try:
        prompt = f"""
        You are an expert venture capital analyst. Analyze the following startup pitch deck content and provide a comprehensive investment memo.
        
        IMPORTANT: For market analysis data (TAM, competitors, industry reports), use Google Search to find current, accurate information.

        CRITICAL WEIGHTAGE INSTRUCTIONS:
        The following weightage percentages MUST be used to calculate the composite risk score and overall conclusion (total = 100%):
        - Team Strength: {weightage.get('team_strength', 20)}%
        - Market Opportunity: {weightage.get('market_opportunity', 20)}%
        - Traction: {weightage.get('traction', 20)}%
        - Claim Credibility: {weightage.get('claim_credibility', 20)}%
        - Financial Health: {weightage.get('financial_health', 20)}%

        
        USE THESE WEIGHTS TO:
        1. Calculate the composite_risk_score (0-100, where lower is better)
        2. Determine the overall_attractiveness in the conclusion
        3. Prioritize analysis depth for higher-weighted factors
        
        Pitch Deck Content:
        {extracted_text[:50000]}
        
        Provide a detailed analysis in the following JSON structure. Use Google Search to find real market data, competitor information, and industry reports:
        
        {{
            "company_overview": {{
                "name": "extracted company name",
                "sector": "primary sector/industry",
                "founders": [
                    {{
                        "name": "founder name",
                        "education": "educational background with institution names",
                        "professional_background": "detailed work experience with companies and roles",
                        "previous_ventures": "prior entrepreneurial experience with outcomes"
                    }}
                ],
                "technologies_used": "detailed description of core technologies, frameworks, and technical stack",
                "key_problems_solved": ["problem 1", "problem 2", "problem 3"]
            }},
            "market_analysis": {{
                "industry_size_and_growth": {{
                    "total_addressable_market": {{
                        "name": "TAM description",
                        "value": "market size with units (use Google Search for current data)",
                        "cagr": "growth rate from recent reports",
                        "source": "cite source with year"
                    }},
                    "serviceable_obtainable_market": {{
                        "name": "SOM description",
                        "value": "realistic market size for this company",
                        "projection": "future projections for next 3-5 years",
                        "cagr": "projected growth rate",
                        "source": "cite source with year"
                    }},
                    "commentary": "detailed market insights and trends"
                }},
                "sub_segment_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
                "competitor_details": [
                    {{
                        "name": "competitor name (search for real competitors)",
                        "headquarters": "HQ location",
                        "founding_year": "year founded",
                        "total_funding_raised": "total funding amount",
                        "funding_rounds": "number of rounds and details",
                        "investors": "list of key investors",
                        "business_model": "how they make money",
                        "revenue_streams": "primary revenue sources",
                        "target_market": "their target customers",
                        "gross_margin": "gross margin % if available",
                        "net_margin": "net margin % if available",
                        "operating_expense": "OpEx details if available",
                        "current_arr": "ARR if publicly known",
                        "current_mrr": "MRR if publicly known",
                        "arr_growth_rate": "growth rate if available",
                        "churn_rate": "customer churn rate if available"
                    }}
                ],
                "reports": [
                    {{
                        "title": "relevant industry report title (search Google)",
                        "source_name": "report publisher name",
                        "source_url": "URL to report",
                        "summary": "2-3 sentence summary of key findings"
                    }}
                ]
            }},
            "business_model": [
                {{
                    "revenue_streams": "revenue stream name (e.g., SaaS Subscriptions)",
                    "description": "detailed description of how this revenue stream works",
                    "target_audience": "specific customer segment for this stream",
                    "percentage_contribution": "estimated % of total revenue",
                    "pricing": "pricing strategy and tiers",
                    "unit_economics": {{
                        "customer_acquisition_cost_CAC": "CAC value with calculation",
                        "lifetime_value_LTV": "LTV value with calculation",
                        "LTV_CAC_Ratio": "ratio and interpretation"
                    }},
                    "scalability": "assessment of scalability for this revenue stream",
                    "additional_revenue_opportunities": ["opportunity 1", "opportunity 2"]
                }},
                ...
            ],
            "financials": {{
                "arr_mrr": {{
                    "current_booked_arr": "current ARR value",
                    "current_mrr": "current MRR value"
                }},
                "burn_and_runway": {{
                    "funding_ask": "amount being raised",
                    "stated_runway": "runway duration with current burn",
                    "implied_net_burn": "monthly burn rate",
                    "gross_margin": "gross margin percentage",
                    "cm1": "Contribution Margin 1 (Revenue - COGS)",
                    "cm2": "Contribution Margin 2 (CM1 - Sales & Marketing)",
                    "cm3": "Contribution Margin 3 (CM2 - R&D)"
                }},
                "funding_history": "previous funding rounds with amounts and investors",
                "valuation_rationale": "justification for current/proposed valuation",
                "projections": [
                    {{"year": "year", "revenue": "projected revenue"}},
                    ...
                ]
            }},
            "claims_analysis": [
                {{
                    "claim": "specific claim from pitch deck",
                    "analysis_method": "methodology used to verify",
                    "input_dataset_length": "number of data points analyzed",
                    "simulation_assumptions": "key assumptions made",
                    "simulated_probability": "probability of claim being accurate (0-100%)",
                    "result": "credibility assessment with reasoning"
                }}
            ],
            "risk_metrics": {{
                "composite_risk_score": <CALCULATED_SCORE>,
                "score_interpretation": "Low (0-40), Medium (41-70), High (71-100)",
                "narrative_justification": "Detailed explanation: Evaluate each factor (Team: {weightage.get('team_strength', 20)}%, Market: {weightage.get('market_opportunity', 20)}%, Traction: {weightage.get('traction', 20)}%, Claims: {weightage.get('claim_credibility', 20)}%, Financials: {weightage.get('financial_health', 20)}%). Calculate composite score = (Team_Score × {weightage.get('team_strength', 20)}/100) + (Market_Score × {weightage.get('market_opportunity', 20)}/100) + (Traction_Score × {weightage.get('traction', 20)}/100) + (Claims_Score × {weightage.get('claim_credibility', 20)}/100) + (Financials_Score × {weightage.get('financial_health', 20)}/100)"
            }},
            "risks_and_mitigation": [
                {{
                    "risk": "Market Risk",
                    "description": "detailed description of the risk",
                    "likelihood": "Low/Medium/High",
                    "impact": "Low/Medium/High",
                    "mitigation": "proposed mitigation strategies"
                }},
                {{
                    "risk": "Technology Risk",
                    "description": "detailed description",
                    "likelihood": "Low/Medium/High",
                    "impact": "Low/Medium/High",
                    "mitigation": "proposed mitigation strategies"
                }},
                {{
                    "risk": "Competitive Risk",
                    "description": "detailed description",
                    "likelihood": "Low/Medium/High",
                    "impact": "Low/Medium/High",
                    "mitigation": "proposed mitigation strategies"
                }},
                {{
                    "risk": "Execution Risk",
                    "description": "detailed description",
                    "likelihood": "Low/Medium/High",
                    "impact": "Low/Medium/High",
                    "mitigation": "proposed mitigation strategies"
                }},
                {{
                    "risk": "Financial Risk",
                    "description": "detailed description",
                    "likelihood": "Low/Medium/High",
                    "impact": "Low/Medium/High",
                    "mitigation": "proposed mitigation strategies"
                }}
            ],
            "conclusion": {{
                "overall_attractiveness": "CRITICAL: Base recommendation on WEIGHTED evaluation. Weightages: Team ({weightage.get('team_strength', 20)}%), Market ({weightage.get('market_opportunity', 20)}%), Traction ({weightage.get('traction', 20)}%), Claims ({weightage.get('claim_credibility', 20)}%), Financials ({weightage.get('financial_health', 20)}%). Start with clear INVEST/PASS/CONDITIONAL recommendation, reference composite risk score, and explain how each percentage-weighted factor influenced the decision. Emphasize the highest-weighted factors more prominently in your reasoning."
            }}
        }}
        
        CRITICAL INSTRUCTIONS FOR RISK_METRICS AND CONCLUSION:
        1. For market_analysis data, USE GOOGLE SEARCH to find current, accurate information
        2. **COMPOSITE RISK SCORE CALCULATION** (weights are already percentages totaling 100%):
           - Evaluate each of the 5 factors (Team, Market, Traction, Claims, Financials) on a 0-100 risk scale
           - Multiply each risk score by its percentage weight and divide by 100
           - Sum the weighted scores to get the composite_risk_score
           - Example: Team Risk=30 (weight {weightage.get('team_strength', 20)}%), Market Risk=50 (weight {weightage.get('market_opportunity', 20)}%)
           - Composite = (30 × {weightage.get('team_strength', 20)}/100) + (50 × {weightage.get('market_opportunity', 20)}/100) + ...
        3. **CONCLUSION REQUIREMENTS**:
           - Start with clear recommendation: "INVEST", "PASS", or "CONDITIONAL INVEST"
           - Reference the composite risk score prominently
           - Explain how each percentage-weighted factor influenced the decision
           - Give MORE weight in your reasoning to factors with HIGHER percentages
           - If a high-weighted factor is weak, emphasize this strongly
        4. Search for real competitors and get their actual funding, metrics, and business details
        5. Find recent industry reports from credible sources (Gartner, McKinsey, CB Insights, etc.)
        6. If information is not available in pitch deck OR via search, use exactly "Not available" (not N/A, Unknown, etc.)
        7. If information is partial/vague, provide what you have but flag it in a note
        8. Ensure all numeric values include units (e.g., "$5M", "25%", "18 months")
        9. Include at least 3-5 real competitors with as much detail as possible
        10. Include at least 2-3 recent industry reports
        11. Analyze at least 3-5 major claims from the pitch deck
        12. Include all 5 risk categories with detailed mitigation strategies
        13. Return ONLY valid JSON, no additional text or markdown
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
                temperature=0.2,
                top_p=0.8,
                top_k=40,
                # max_output_tokens=8192,
                max_output_tokens=16384
            )
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Remove markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
        
        # Parse JSON
        analysis = json.loads(response_text)
        
        # Validate required fields
        required_fields = [
            'company_overview', 'market_analysis', 'business_model',
            'financials', 'claims_analysis', 'risk_metrics',
            'risks_and_mitigation', 'conclusion'
        ]
        
        for field in required_fields:
            if field not in analysis:
                print(f"Warning: Missing required field: {field}")
                analysis[field] = {}
        
        # Add weightage metadata to the analysis
        analysis['_weightage_used'] = weightage
        
        return analysis
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Gemini: {str(e)}")
        print(f"Response text: {response_text[:500]}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to parse analysis response. Invalid JSON format."
        )
    except Exception as e:
        print(f"Error in Gemini analysis: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to analyze content: {str(e)}"
        )

async def recalculate_risk_and_conclusion(
    existing_memo: Dict[str, Any], 
    extracted_text: str,
    weightage: Dict[str, int]
) -> Dict[str, Any]:
    """
    Recalculate ONLY risk_metrics and conclusion based on new weightage
    Uses both extracted text and existing memo for full context
    Keeps all other sections unchanged
    """
    try:
        # Extract key information from existing memo for context
        company_name = existing_memo.get('company_overview', {}).get('name', 'Unknown')
        sector = existing_memo.get('company_overview', {}).get('sector', 'Unknown')
        
        prompt = f"""
You are a VC analyst recalculating risk assessment with NEW weightage.

ORIGINAL PITCH DECK CONTENT (for reference):
{extracted_text[:15000]}

EXISTING ANALYSIS:
Company: {company_name} | Sector: {sector}

Team:
{json.dumps(existing_memo.get('company_overview', {}), indent=2)[:1000]}

Market:
{json.dumps(existing_memo.get('market_analysis', {}), indent=2)[:2000]}

Financials:
{json.dumps(existing_memo.get('financials', {}), indent=2)[:1000]}

Claims:
{json.dumps(existing_memo.get('claims_analysis', []), indent=2)[:1000]}

NEW WEIGHTAGE (total=100%):
- Team Strength: {weightage.get('team_strength', 20)}%
- Market Opportunity: {weightage.get('market_opportunity', 20)}%
- Traction: {weightage.get('traction', 20)}%
- Claim Credibility: {weightage.get('claim_credibility', 20)}%
- Financial Health: {weightage.get('financial_health', 20)}%

TASK: Recalculate risk_metrics and conclusion using NEW weightage.

CALCULATION METHOD:
1. Review ORIGINAL pitch deck + EXISTING analysis
2. Score each factor 0-100 (higher = riskier):
   - Team: founder experience, completeness
   - Market: TAM size, growth, competition
   - Traction: ARR/MRR, growth rate, customers
   - Claims: evidence vs claims ratio
   - Financials: burn rate, runway, margins
3. Apply formula: Composite = (Team×{weightage.get('team_strength')}/100) + (Market×{weightage.get('market_opportunity')}/100) + (Traction×{weightage.get('traction')}/100) + (Claims×{weightage.get('claim_credibility')}/100) + (Financials×{weightage.get('financial_health')}/100)

Return ONLY this JSON (complete all fields):

{{
    "risk_metrics": {{
        "composite_risk_score": 0,
        "score_interpretation": "Low (0-40), Medium (41-70), High (71-100)",
        "narrative_justification": "Explain calculation: Team risk X × {weightage.get('team_strength')}%, Market risk Y × {weightage.get('market_opportunity')}%, etc. Show how new weights changed the score."
    }},
    "conclusion": {{
        "overall_attractiveness": "Start with INVEST/PASS/CONDITIONAL. Reference composite score. Explain how new weightage (Team {weightage.get('team_strength')}%, Market {weightage.get('market_opportunity')}%, Traction {weightage.get('traction')}%, Claims {weightage.get('claim_credibility')}%, Financials {weightage.get('financial_health')}%) influenced decision."
    }}
}}

CRITICAL: Return ONLY valid complete JSON. No markdown.
"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
            )
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Remove markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
        
        # Parse JSON
        recalculated = json.loads(response_text)
        
        # Validate required fields
        if 'risk_metrics' not in recalculated:
            raise ValueError("Missing risk_metrics in response")
        if 'conclusion' not in recalculated:
            raise ValueError("Missing conclusion in response")
        
        # Validate nested fields
        if 'composite_risk_score' not in recalculated['risk_metrics']:
            raise ValueError("Missing composite_risk_score")
        if 'overall_attractiveness' not in recalculated['conclusion']:
            raise ValueError("Missing overall_attractiveness")
        
        return recalculated
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Gemini: {str(e)}")
        print(f"Full response text:\n{response_text}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to parse recalculation response. Response was truncated or invalid."
        )
    except Exception as e:
        print(f"Error recalculating risk and conclusion: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to recalculate: {str(e)}"
        )

async def chat_with_ai(memo: Dict[str, Any], company_name: str, sector: str, chat_history: list, user_message: str) -> str:
    """Handle AI chat for founder interview"""
    try:
        context = f"""
        You are an AI investment analyst conducting an interview with a startup founder.
        
        Company: {company_name}
        Sector: {sector}
        
        Current Investment Memo Summary:
        {json.dumps(memo, indent=2)[:5000]}
        
        Your goal is to gather missing or unclear information to complete the investment analysis.
        Focus on:
        1. Missing financial data (ARR, MRR, burn rate, margins)
        2. Unclear market assumptions
        3. Team background gaps
        4. Unsubstantiated claims
        5. Customer traction details
        6. Technology and IP details
        7. Competitive advantages
        
        Be professional, concise, and focused. Ask one question at a time.
        
        Chat History:
        {json.dumps(chat_history[-10:], indent=2)}
        
        Founder's latest message: {user_message}
        
        Respond naturally and ask relevant follow-up questions.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=context
        )
        
        return response.text
    
    except Exception as e:
        print(f"Error in AI chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}")
