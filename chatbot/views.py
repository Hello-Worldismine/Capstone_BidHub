from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
import json
from django.shortcuts import render
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

ROLE_PROMPT = """
너는 오직 블록체인과 부동산 경매 관련 질문에만 답변하는 챗봇입니다.
반드시 한국어 존댓말을 사용하세요.
"""

ALLOWED_KEYWORDS = ["블록체인", "비트코인", "이더리움", "경매", "부동산", "입찰"]

def is_allowed_question(question):
    return any(keyword in question for keyword in ALLOWED_KEYWORDS)

@csrf_exempt
def chat_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message', '')

        if not is_allowed_question(user_input):
            return JsonResponse({'reply': '죄송합니다. 저는 블록체인과 부동산 경매에 관한 내용만 안내해 드리고 있습니다.'})

        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"{ROLE_PROMPT.strip()}\n\n사용자 질문: {user_input}"
        response = model.generate_content(prompt)

        reply_text = response.text[:500]  # 필요 시 길이 제한
        return JsonResponse({'reply': reply_text})

    return JsonResponse({'error': 'Invalid request'}, status=400)

def chat_page(request):
    return render(request, 'chatbot/chat.html')
