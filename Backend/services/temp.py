from typing import Dict, Any, List
from google import genai
from google.genai.types import GenerateContentConfig
from config.settings import settings
import json

client = genai.Client(
    vertexai=True,
    project=settings.GCP_PROJECT_ID,
    location=settings.GCP_LOCATION
)

async def chat_with_founder(
    interview_data: Dict[str, Any],
    user_message: str,
    chat_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Natural conversational AI that adapts to founder's responses
    """
    
    company_name = interview_data.get('company_name', 'your startup')
    sector = interview_data.get('sector', 'your industry')
    founder_name = interview_data.get('founder_name', 'Founder')
    issues = interview_data.get('issues', [])
    gathered_info = interview_data.get('gathered_info', {})
    cannot_answer_fields = interview_data.get('cannot_answer_fields', [])
    
    # ✅ Get all original issue field names
    all_issue_fields = [issue['field'] for issue in issues]
    
    # ✅ Only count gathered_info that matches actual issue fields
    gathered_issue_fields = [f for f in gathered_info.keys() if f in all_issue_fields]
    
    # Build what we still need - EXCLUDE fields already gathered or can't answer
    still_needed = [
        {
            'field': issue['field'],
            'question': issue['question'],
            'category': issue['category'],
            'importance': issue['importance'],
            'status': issue['status']
        }
        for issue in issues
        if issue['field'] not in gathered_issue_fields and issue['field'] not in cannot_answer_fields
    ]
    
    # Get recent context
    recent_context = chat_history[-10:] if len(chat_history) > 10 else chat_history
    
    # Get next 3 questions to ask
    next_questions = [q['question'] for q in still_needed[:3]]
    
    # ✅ Debug logging
    print(f"📋 Total issues: {len(all_issue_fields)}")
    print(f"✅ Gathered (matching issues): {len(gathered_issue_fields)}")
    print(f"❌ Cannot answer: {len(cannot_answer_fields)}")
    print(f"⏳ Still needed: {len(still_needed)}")
    print(f"📊 Progress: {len(gathered_issue_fields) + len(cannot_answer_fields)}/{len(all_issue_fields)}")
    
    will_be_closing = len(still_needed) <= 0
    
    # Build conversation prompt
    if will_be_closing:
        # ✅ CLOSING MESSAGE
        prompt = f"""
You are Sarah, a friendly investment analyst. You just finished interviewing {founder_name} about {company_name}.

## CONTEXT:
- We've covered all topics we needed to discuss
- Total topics: {len(all_issue_fields)}
- Answered: {len(gathered_issue_fields)}
- Couldn't answer: {len(cannot_answer_fields)}
- Founder's last message: "{user_message}"

## YOUR TASK:
Write a warm, professional CLOSING message that:
1. Thanks them for their time and openness
2. Summarizes what you'll do next (update investment memo, share feedback)
3. Encourages them about their company
4. Mentions when they might expect to hear back (within 2-3 weeks)
5. Leaves them feeling positive

Keep it 60-100 words. Be warm and genuine, not robotic.

Closing message:
"""
    else:
        # ✅ NORMAL CONTINUATION
        prompt = f"""
You are Sarah, a friendly investment analyst talking with {founder_name} about {company_name} ({sector}).

## CONTEXT:
- Progress: {len(gathered_issue_fields) + len(cannot_answer_fields)}/{len(all_issue_fields)} topics covered
- Founder's latest message: "{user_message}"
- Fields they already said they don't know: {json.dumps(cannot_answer_fields[:5])}

## NEXT 3 QUESTIONS TO ASK (in priority order):
1. {next_questions[0] if len(next_questions) > 0 else 'Tell me about your financials?'}
2. {next_questions[1] if len(next_questions) > 1 else 'Tell me about your team?'}
3. {next_questions[2] if len(next_questions) > 2 else 'Tell me about your market?'}

## RECENT CONVERSATION:
{json.dumps(recent_context[-6:], indent=2)}

## YOUR RULES:
1. Be warm, conversational, human-like
2. Acknowledge their answer briefly (1-2 sentences)
3. THEN ASK THE NEXT QUESTION (required!)
4. If they say "don't know":
   - First time → Try ONE different angle OR ask for rough estimate
   - After that → Move to DIFFERENT question, don't repeat
5. One question at a time, 40-80 words total
6. Make it feel like coffee chat, not interrogation
7. MUST END WITH A QUESTION MARK
8. DO NOT ask questions about topics they already said they don't know

## CRITICAL: YOUR RESPONSE MUST:
✓ Acknowledge their answer
✓ Ask ONE of the next 3 questions above
✓ End with "?"

Based on all this, respond with acknowledgment + next question:
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.85,
                max_output_tokens=1000,
                top_p=0.95
            )
        )
        
        if response is None or not hasattr(response, 'text'):
            raise ValueError("Invalid API response")
        
        ai_message = response.text.strip()
        
        if not ai_message:
            raise ValueError("Empty response from AI")
        
        # ✅ Only add question mark if NOT closing message
        if not will_be_closing:
            if not ai_message.endswith('?'):
                if not any(ai_message.endswith(p) for p in ['?', '!', '.']):
                    ai_message += '?'
                elif ai_message.endswith('.'):
                    if '?' not in ai_message:
                        ai_message = ai_message[:-1] + '?'
        
    except Exception as e:
        print(f"❌ Chat Error: {str(e)}")
        if will_be_closing:
            ai_message = f"Thank you so much for your time, {founder_name}! We've gathered excellent insights about {company_name}. I'll update our investment memo and get back to you within 2-3 weeks with our feedback. Best of luck with everything!"
        else:
            next_q = still_needed[0]['question'] if still_needed else "What else can you tell me?"
            ai_message = f"Thanks for sharing! {next_q}"
    
    # Extract what was gathered from this turn
    completion_check = await analyze_and_extract(
        issues,
        gathered_info,
        cannot_answer_fields,
        chat_history + [
            {"role": "user", "message": user_message},
            {"role": "assistant", "message": ai_message}
        ]
    )
    
    return {
        "message": ai_message,
        "is_complete": completion_check['is_complete'],
        "gathered_info": completion_check['gathered_info'],
        "cannot_answer_fields": completion_check.get('cannot_answer_fields', [])
    }


async def analyze_and_extract(
    issues: List[Dict[str, str]],
    gathered_info: Dict[str, Any],
    existing_cannot_answer: List[str],
    chat_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Extract information from latest conversation turn
    """
    
    user_messages = [msg for msg in chat_history if msg['role'] == 'user']
    
    if len(user_messages) < 2:
        return {
            "is_complete": False,
            "gathered_info": gathered_info,
            "still_pending": [i['field'] for i in issues],
            "cannot_answer_fields": []
        }
    
    # ✅ Get all issue field names
    all_issue_fields = [issue['field'] for issue in issues]
    
    # Build conversation - only recent messages
    conversation = []
    for msg in chat_history[-10:]:
        role = "Analyst" if msg['role'] == 'assistant' else "Founder"
        conversation.append(f"{role}: {msg['message']}")
    
    # What we're still looking for
    fields_needed = [
        {
            'field': issue['field'],
            'question': issue['question'],
            'category': issue['category']
        }
        for issue in issues
        if issue['field'] not in gathered_info
    ]
    
    # Ask AI to analyze ONLY latest exchange
    analysis_prompt = f"""
Analyze the LATEST founder response to extract information.

## FIELDS WE NEED:
{json.dumps(fields_needed[:10], indent=2)}

## ALREADY HAVE:
{json.dumps([f for f in gathered_info.keys() if f in all_issue_fields])}

## LATEST CONVERSATION (last 4 messages):
{json.dumps(conversation[-4:], indent=2)}

## YOUR TASK:
1. Extract information from the LATEST founder message ONLY
2. Match extracted info to the field names in "FIELDS WE NEED"
3. Note if founder said "don't know" in this latest response

Return JSON:
{{
    "extracted": {{
        "exact_field_name_from_fields_we_need": {{
            "value": "what they said",
            "confidence": "high/medium/low"
        }}
    }},
    "cannot_answer": ["exact_field_name_from_fields_we_need"]
}}

CRITICAL RULES:
- Use EXACT field names from "FIELDS WE NEED" list
- Extract ONLY from latest founder message
- "cannot_answer" = fields they said "don't know" to in THIS message only
- Confidence high = clear answer, medium = partial answer, low = vague
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=analysis_prompt,
            config=GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                max_output_tokens=2048
            )
        )
        
        if response is None or not hasattr(response, 'text') or response.text is None:
            raise ValueError("Invalid API response")
        
        response_text = response.text.strip()
        
        if not response_text:
            raise ValueError("Empty response")
        
        result = json.loads(response_text)
        
        # ✅ Merge extracted info - ONLY if field name matches issues
        merged = {**gathered_info}
        for field, data in result.get('extracted', {}).items():
            # Only add if it's a valid issue field
            if field in all_issue_fields and data.get('confidence') in ['high', 'medium']:
                merged[field] = data
        
        # ✅ Get NEW cannot_answer fields from this response
        new_cannot_answer = [f for f in result.get('cannot_answer', []) if f in all_issue_fields]
        
        # ✅ Calculate progress based on ACTUAL issue fields only
        gathered_count = len([f for f in merged.keys() if f in all_issue_fields])
        total_cannot_answer = len(set(existing_cannot_answer + new_cannot_answer))
        total_attempted = gathered_count + total_cannot_answer
        total_issues = len(all_issue_fields)
        
        # ✅ Simple: Complete when ALL issues attempted
        is_complete = (total_attempted >= total_issues)
        
        print(f"📊 Extraction result:")
        print(f"   - Gathered: {gathered_count}/{total_issues}")
        print(f"   - Cannot answer: {total_cannot_answer}")
        print(f"   - Total attempted: {total_attempted}/{total_issues}")
        print(f"   - Complete: {is_complete}")
        
        return {
            "is_complete": is_complete,
            "gathered_info": merged,
            "still_pending": [f for f in all_issue_fields if f not in merged.keys() and f not in existing_cannot_answer],
            "cannot_answer_fields": new_cannot_answer  # Only NEW ones from this turn
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {str(e)}")
        return {
            "is_complete": False,
            "gathered_info": gathered_info,
            "still_pending": [i['field'] for i in fields_needed],
            "cannot_answer_fields": []
        }
    except Exception as e:
        print(f"❌ Analysis Error: {str(e)}")
        return {
            "is_complete": False,
            "gathered_info": gathered_info,
            "still_pending": [i['field'] for i in fields_needed],
            "cannot_answer_fields": []
        }
