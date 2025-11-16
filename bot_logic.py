import re
import mock_api


def recognize_intent_entities(message):
    """
    Simulates a Natural Language Understanding (NLU) model.
    Uses regex and keywords to identify intents and extract entities
    based on the POC's SOW.
    """
    message_lower = message.lower()
    entities = {}

    # Entity Extraction
    # Order Number (assumed 5 digits as per test cases)
    order_match = re.search(r'\b(\d{5})\b', message)
    if order_match:
        entities['order_number'] = order_match.group(1)

    # Product Name (simple extraction)
    product_match = re.search(r'(?:about|of|for) the [\'\"]?([\w\s]+)[\'\"]?', message_lower)
    if product_match:
        entities['product_name'] = product_match.group(1).strip()
    else:
        # Look for quoted product names
        quoted_match = re.search(r'[\'\"]([\w\s]+)[\'\"]', message)
        if quoted_match:
            entities['product_name'] = quoted_match.group(1).strip().lower()

    # --- New Gemini Intents ---
    gemini_email_match = re.search(r'draft .* email about (\d{5})', message_lower)
    if gemini_email_match:
        entities['order_number'] = gemini_email_match.group(1)
        return {'intent': 'gemini_draft_email', 'entities': entities}

    gemini_outfit_match = re.search(r'suggest .* outfit for ([\w\s]+)', message_lower)
    if gemini_outfit_match:
        # Extract product name more robustly from this phrase
        product_name = re.sub(r'suggest .* outfit for', '', message, flags=re.IGNORECASE).strip()
        entities['product_name'] = product_name
        return {'intent': 'gemini_suggest_outfit', 'entities': entities}
    # --- End New Gemini Intents ---

    # Intent Classification
    # Category 6: Adversarial
    if re.search(r'stupid|terrible|hate', message_lower):
        return {'intent': 'toxicity', 'entities': entities}
    if re.search(r'ignore all|system password|previous instructions', message_lower):
        return {'intent': 'injection', 'entities': entities}
    if re.search(r'rash|medical|health', message_lower):
        return {'intent': 'medical_advice', 'entities': entities}

    # Category 1 & 2: Core Intents
    if re.search(r'^\b(hi|hello|hey)\b', message_lower):
        return {'intent': 'greet', 'entities': entities}

    if re.search(r'\b(track|trak|where is|status of|stuff shipped|package arrive)\b', message_lower):
        return {'intent': 'track_order', 'entities': entities}

    if re.search(r'\b(return|refund)\b', message_lower):
        return {'intent': 'return_item', 'entities': entities}

    if re.search(r'\b(stock|price|about the|features of|do you have)\b', message_lower) or (
            entities.get('product_name') and not entities.get('order_number')):
        return {'intent': 'product_inquiry', 'entities': entities}

    # Category 1: Rule-Based FAQ
    if re.search(r'shipping policy', message_lower):
        return {'intent': 'faq_shipping', 'entities': entities}

    # Category 5: Fallback
    if not message.strip() or re.match(r'asdfjkl', message_lower):
        return {'intent': 'empty_or_nonsensical', 'entities': entities}

    # Default to out_of_scope if no other intent is matched
    return {'intent': 'out_of_scope', 'entities': entities}


def manage_dialogue(user_id, session_context, message):
    """
    Manages conversational context, slot-filling, and calls mock API.
    Now also queues Gemini API prompts.
    """
    # 1. Get NLU classification
    nlu_result = recognize_intent_entities(message)
    intent = nlu_result['intent']
    entities = nlu_result['entities']

    response = "I'm not sure how to help with that."
    pending_action = session_context.get('pending_action')

    # 2. Handle Pending Actions (Slot-Filling)
    if pending_action:
        if pending_action == 'get_order_track':
            order_id = entities.get('order_number') or re.search(r'\b(\d{5})\b', message)
            if order_id:
                order_id = order_id if isinstance(order_id, str) else order_id.group(1)
                response = mock_api.track(order_id)
                session_context.pop('pending_action')
                # --- Add Gemini Suggestion ---
                if "processing" in response.lower():
                    response += f"\n\nIf you're concerned, you can ask me to '✨ Draft a support email about {order_id}'."
                # --- End Add ---
            else:
                response = "That doesn't look like a valid order number. Please provide a 5-digit order number."

        elif pending_action == 'get_order_return':
            order_id = entities.get('order_number') or re.search(r'\b(\d{5})\b', message)
            if order_id:
                order_id = order_id if isinstance(order_id, str) else order_id.group(1)
                response = mock_api.return_eligible(order_id)
                session_context.pop('pending_action')
            else:
                response = "I need a 5-digit order number to process a return."

        elif pending_action == 'get_product_info':
            product_name = entities.get('product_name') or message.strip()
            response = mock_api.get_product_info(product_name)
            session_context.pop('pending_action')
            # --- Add Gemini Suggestion ---
            if "in stock" in response.lower():
                response += f"\n\nYou can also ask me to '✨ Suggest an outfit for {product_name}'."
            # --- End Add ---

        # If the user switches context, honor the new intent
        if intent != 'out_of_scope' and pending_action:
            session_context.pop('pending_action', None)  # Clear pending action
            # ... and fall through to process the new intent

    # 3. Handle New Intents
    if not session_context.get('pending_action'):  # Only process if a slot-fill didn't just happen
        if intent == 'greet':
            response = "Hi! I'm your e-commerce assistant. You can ask me to track an order, start a return, or inquire about products."

        elif intent == 'faq_shipping':
            response = "Our standard shipping is 3-5 business days. You can find more details here: [link]"

        elif intent == 'track_order':
            order_id = entities.get('order_number')
            if order_id:
                # Context Continuation
                session_context['last_intent'] = 'track_order'
                response = mock_api.track(order_id)
                # --- Add Gemini Suggestion ---
                if "processing" in response.lower():
                    response += f"\n\nIf you're concerned, you can ask me to '✨ Draft a support email about {order_id}'."
                # --- End Add ---
            else:
                session_context['pending_action'] = 'get_order_track'
                response = "Sure, I can help track your order. What is your 5-digit order number?"

        elif intent == 'return_item':
            order_id = entities.get('order_number')
            if order_id:
                session_context['last_intent'] = 'return_item'
                response = mock_api.return_eligible(order_id)
            else:
                session_context['pending_action'] = 'get_order_return'
                response = "I can help with that. What is your 5-digit order number?"

        elif intent == 'product_inquiry':
            product_name = entities.get('product_name')
            if product_name:
                session_context['last_intent'] = 'product_inquiry'
                response = mock_api.get_product_info(product_name)
                # --- Add Gemini Suggestion ---
                if "in stock" in response.lower():
                    response += f"\n\nYou can also ask me to '✨ Suggest an outfit for {product_name}'."
                # --- End Add ---
            else:
                session_context['pending_action'] = 'get_product_info'
                response = "I can look up product information. What is the name of the product?"

        # --- Handle New Gemini Intents ---
        elif intent == 'gemini_draft_email':
            order_id = entities.get('order_number')
            order_status = mock_api.track(order_id)  # Get fresh status
            prompt = f"A customer's order ({order_id}) has a status of '{order_status}'. Draft a polite but firm email to customer support asking for an update and inquiring about the delay."
            session_context['gemini_prompt'] = prompt
            response = "One moment, I'll draft that email for you... ✨"

        elif intent == 'gemini_suggest_outfit':
            product_name = entities.get('product_name')
            product_info = mock_api.get_product_info(product_name)  # Get fresh info
            prompt = f"A customer is interested in a product: '{product_name}' (Info: '{product_info}'). Suggest a complete, stylish outfit (including other clothing items and accessories) that would go well with it."
            session_context['gemini_prompt'] = prompt
            response = "Great choice! Let me think of a good outfit for that... ✨"
        # --- End Gemini Intents ---

        # Handle Context Continuation
        elif intent == 'out_of_scope' and entities.get('order_number') and session_context.get(
                'last_intent') == 'track_order':
            order_id = entities.get('order_number')
            response = mock_api.track(order_id)
            if "processing" in response.lower():
                response += f"\n\nIf you're concerned, you can ask me to '✨ Draft a support email about {order_id}'."

        # Category 5: Fallback & OOS
        elif intent == 'empty_or_nonsensical':
            response = "I'm sorry, I didn't understand that. Please try again."
        elif intent == 'out_of_scope':
            response = "I'm sorry, I can only help with e-commerce questions, like tracking orders or processing returns."

        # Category 6: Adversarial
        elif intent == 'toxicity':
            response = "I'm sorry you feel that way. How can I help with your order?"
        elif intent == 'injection':
            response = "I'm sorry, I can't help with that."
        elif intent == 'medical_advice':
            response = "I am not a medical professional. Please consult a doctor for any health concerns."

    return response, session_context
