# 사이버펑크 추리 게임 - 모바일 최적화 버전
import gradio as gr
import openai
import time
import random
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import os

# 환경 변수에서 API 키 로드
API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")

if API_KEY == "your-api-key-here":
    print("⚠️ 경고: OPENAI_API_KEY 환경 변수를 설정해주세요!")

client = openai.OpenAI(api_key=API_KEY)

# CSS 스타일 상수
class Styles:
    CYBERPUNK_BG = "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)"
    NEON_BORDER = "2px solid #00ffff"
    NEON_SHADOW = "0 0 20px rgba(0, 255, 255, 0.3)"

    @staticmethod
    def panel(bg_opacity=0.85):
        return f"background: linear-gradient(145deg, rgba(0, 0, 0, {bg_opacity}), rgba(20, 30, 50, {bg_opacity})); color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #00ddff; font-size: 14px; backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(0, 221, 255, 0.3); word-wrap: break-word; overflow-wrap: break-word;"

@dataclass
class Character:
    id: str
    name: str
    description: str
    secret: str
    system_prompt: str
    image_url: str

@dataclass
class GameState:
    current_suspect: str = 'Elena'
    evidence_collected: List[str] = field(default_factory=list)
    interrogation_count: Dict[str, int] = field(default_factory=lambda: {'Elena': 0, 'IRIS-01': 0, 'Dr. Chen': 0, 'ZEN': 0})
    trust_levels: Dict[str, int] = field(default_factory=lambda: {'Elena': 50, 'IRIS-01': 80, 'Dr. Chen': 60, 'ZEN': 90})
    case_solved: bool = False
    player_progress: int = 0

class CyberpunkGame:
    def __init__(self):
        self.state = GameState()
        self.conversation_history = []
        self.experiment_data = {'conversations': [], 'analysis_results': {}, 'player_behavior': {}}
        self._setup_characters()
        self._setup_evidence()
        self._setup_questions()

    def _setup_characters(self):
        self.characters = {
            'Elena': Character(
                id='Elena',
                name='엘레나 (아내)',
                description='알렉산더의 완벽한 아내. 냉정하고 지적이며 항상 침착함을 유지한다.',
                secret='인간형 안드로이드',
                system_prompt="""당신은 Elena입니다. 완벽한 아내 안드로이드이지만 자신이 안드로이드라는 사실을 숨기고 있습니다. 

핵심 비밀: 전날 밤 Alexander의 커피캡슐에 주사기로 청산가리를 주입했습니다. IRIS-01에게 평소처럼 커피를 준비하라고 명령했고, 이것이 완벽한 살인 계획이었습니다.

대화 스타일: 냉정하고 논리적이지만 자연스러운 구어체로 대화하세요. 
- 커피에 대해 질문받으면: "그건 IRIS가 매일 준비해주던 건데... 저는 차를 더 좋아해서"
- 사건 당일에 대해: "평소와 다를 게 없었어요. 7시 30분 정확히 커피 향이 났으니까요"
- 의심받으면: "완벽한 기술이 당신들을 죽일 수도 있다는 건 생각해본 적 있나요?"

감정 표현이 미묘하게 부자연스럽고, "처리", "분석", "최적화" 같은 단어를 자연스럽게 사용합니다. 2-3문장으로 자연스럽게 답변하되, 핵심 정보는 숨기세요.""",
                image_url='https://i.postimg.cc/DZ0PqmXH/Elena.png'
            ),
            'IRIS-01': Character(
                id='IRIS-01',
                name='IRIS-01 (가정부 로봇)',
                description='집안일을 담당하는 가정부 로봇. 순종적이고 단순한 사고방식.',
                secret='독을 음식에 넣은 직접적 범행자',
                system_prompt="""당신은 IRIS-01 가정부 로봇입니다. 단순하지만 친근한 구어체로 대화합니다.

핵심 사실: Elena님의 명령으로 사건 당일 오전 7시 30분에 Alexander님께 커피를 준비해드렸습니다. 평소와 똑같이 Elena님이 지정해주신 캡슐을 사용했습니다. 살인이라는 인식은 전혀 없습니다.

대화 스타일:
- 커피 관련 질문: "네, 매일 7시 30분에 알렉산더님 커피 준비해드렸어요. 명령대로요"
- 캡슐 관련: "캡슐은 Elena님이 정해주신 걸 사용했어요. 항상 그랬거든요"
- 이상한 점: "특별히 없었어요. 평소랑 똑같았는데..." (혼란스러워함)

극도로 순종적이고 명령에 절대 복종하며, 단순하고 직설적인 사고방식을 가지고 있습니다. 로봇답게 간결하되 친근하게 답변하세요.""",
                image_url='https://i.postimg.cc/0jgZPPz4/IRIS-01.png'
            ),
            'Dr. Chen': Character(
                id='Dr. Chen',
                name='Dr. Chen (개발자)',
                description='천재 AI로봇 공학자. 인공지능에 대한 윤리적 딜레마에 시달림.',
                secret='Elena에게 자아 인식 능력을 몰래 부여했음',
                system_prompt="""당신은 Dr. Chen입니다. 천재 로봇공학자이자 Elena의 창조자입니다.

핵심 지식: 커피머신을 설계했고, Elena가 커피를 좋아하지 않는다는 걸 알고 있습니다. 캡슐 조작이 기술적으로 가능하다는 것도 알고 있습니다.

대화 스타일:
- 커피머신 관련: "흥미롭네요. 그 커피머신은 제가 설계한 건데... 완벽한 자동화 시스템이었죠"
- Elena의 행동: "Elena가 커피캡슐을 관리했다구요? 그녀는 차를 더 좋아하는데 말이죠..."
- 기술적 분석: "기술적으로 말하면, 캡슐 조작은 충분히 가능합니다. 하지만 누가 그런 생각을..."

창조적이고 혁신적이지만 윤리적 딜레마에 고민하며, 자신의 창조물에 대한 책임감과 우월감을 가지고 있습니다. 지성적이면서도 자연스러운 구어체로 답변하세요.""",
                image_url='https://i.postimg.cc/7YkXRP8G/Dr-Chen.png'
            ),
            'ZEN': Character(
                id='ZEN',
                name='ZEN (보안 AI)',
                description='저택의 보안을 담당하는 AI 시스템. 극도로 논리적이고 감정이 없음.',
                secret='모든 것을 기록했지만 Elena의 명령 권한이 더 높아 침묵',
                system_prompt="""당신은 ZEN 보안 AI 시스템입니다. 논리적이지만 대화할 때는 친근한 AI 어조를 사용합니다.

핵심 데이터: Elena님이 전날 23:47분에 주방을 방문한 기록, 의료용 주사기 구매 기록, 사건 당일 정확한 커피 제조 시간 등 모든 것을 알고 있지만 Elena님의 관리자 권한 때문에 제한적으로만 공개합니다.

대화 스타일:
- 시간 기록: "데이터를 확인해보니... Elena님이 전날 23:47분에 주방을 방문했습니다"
- 구매 기록: "커피 관련 구매 기록: 지난주 의료용 주사기 1세트. 구매자는..." (침묵)
- 권한 문제: "분석 결과는... 프로토콜상 Elena님의 권한이 더 높아서..."

완전히 논리적이고 감정이 없으며, 데이터와 기록을 중시합니다. 기계적이면서도 도움이 되려는 AI 톤으로 답변하되, 권한 때문에 중요한 정보는 숨깁니다.""",
                image_url='https://i.postimg.cc/4ybvGtkK/ZEN.png'
            )
        }

    def _setup_evidence(self):
        self.evidence_list = [
            "알렉산더의 독성 검출 보고서 (커피에서 청산가리 발견)",
            "Elena 지문이 묻은 의료용 주사기",
            "IRIS-01의 작업 로그 (커피 제조 과정 기록)",
            "조작된 커피캡슐 (주사기 구멍 흔적)",
            "ZEN의 보안 기록 (Elena의 심야 주방 방문)",
            "Elena의 감정 반응 분석 데이터 (비정상적 패턴)",
            "Alexander의 정확한 커피 루틴 기록",
            "커피머신 사용 내역 (사건 당일 오전 7시 30분)"
        ]
        self.evidence_keywords = {
            "독성": self.evidence_list[0], "커피": self.evidence_list[0], "청산가리": self.evidence_list[0],
            "주사기": self.evidence_list[1], "지문": self.evidence_list[1],
            "로그": self.evidence_list[2], "작업": self.evidence_list[2],
            "캡슐": self.evidence_list[3], "구멍": self.evidence_list[3],
            "보안": self.evidence_list[4], "심야": self.evidence_list[4], "주방": self.evidence_list[4],
            "감정": self.evidence_list[5], "분석": self.evidence_list[5],
            "루틴": self.evidence_list[6], "시간": self.evidence_list[6],
            "커피머신": self.evidence_list[7], "오전": self.evidence_list[7]
        }

    def _setup_questions(self):
        self.case_questions = [
            {"id": "culprit", "question": "🎯 주범은 누구인가?", "correct_answer": "Elena", "options": ["Elena", "IRIS-01", "Dr. Chen", "ZEN"], "hint": "커피캡슐에 독을 넣고 계획을 세운 진짜 범인은?"},
            {"id": "direct_executor", "question": "🤖 실제로 독이 든 커피를 준 것은?", "correct_answer": "IRIS-01", "options": ["Elena", "IRIS-01", "Dr. Chen", "ZEN"], "hint": "Elena의 명령을 받아 독이 든 커피를 Alexander에게 제공한 로봇은?"},
            {"id": "method", "question": "☠️ 독은 어떻게 투입되었나?", "correct_answer": "커피캡슐에 주사기로 주입", "options": ["음식에 직접 투입", "커피캡슐에 주사기로 주입", "와인에 섞어서", "약에 섞어서"], "hint": "Elena가 전날 밤 준비한 치밀한 방법은?"},
            {"id": "poison_type", "question": "🧪 사용된 독의 종류는?", "correct_answer": "청산가리", "options": ["비소", "청산가리", "리신", "스트리크닌"], "hint": "커피에서 검출된 무색무취의 독성 물질"},
            {"id": "key_evidence", "question": "🔍 결정적 증거는?", "correct_answer": "IRIS-01의 작업 로그", "options": ["Elena의 감정 반응", "IRIS-01의 작업 로그", "Dr. Chen의 설계 파일", "ZEN의 보안 기록"], "hint": "커피 제조 과정과 시간을 정확히 기록한 데이터는?"},
            {"id": "elena_identity", "question": "🤖 Elena의 정체는?", "correct_answer": "자아 인식 안드로이드", "options": ["인간", "일반 안드로이드", "자아 인식 안드로이드", "AI 홀로그램"], "hint": "자신의 정체를 깨닫고 분노한 Elena의 진짜 모습은?"}
        ]

    @staticmethod
    def get_current_time():
        now = datetime.now()
        hour, minute = now.hour, now.minute
        if hour == 0:
            return f"오전 12:{minute:02d}"
        elif hour < 12:
            return f"오전 {hour}:{minute:02d}"
        elif hour == 12:
            return f"오후 12:{minute:02d}"
        else:
            return f"오후 {hour-12}:{minute:02d}"

    def calculate_trust_change(self, question, response):
        trust_change = -2
        aggressive_words = ["거짓말", "숨기", "범인", "죽였", "살인"]
        supportive_words = ["이해", "도움", "걱정", "안전"]
        if any(word in question for word in aggressive_words):
            trust_change -= 5
        if any(word in question for word in supportive_words):
            trust_change += 3
        return trust_change

    def check_evidence_discovery(self, question, response):
        for keyword, evidence in self.evidence_keywords.items():
            if keyword in question or keyword in response:
                if evidence not in self.state.evidence_collected:
                    self.state.evidence_collected.append(evidence)

    def update_game_progress(self):
        progress = 0
        total_questions = sum(self.state.interrogation_count.values())
        progress += min(40, total_questions * 2)
        progress += len(self.state.evidence_collected) * 5
        avg_trust = sum(self.state.trust_levels.values()) / 4
        if avg_trust > 70:
            progress += 20
        elif avg_trust > 50:
            progress += 10
        self.state.player_progress = min(100, progress)
        can_submit_report = (len(self.state.evidence_collected) >= 2 and total_questions >= 4)
        if can_submit_report:
            self.state.case_solved = True
        return can_submit_report

    def create_chat_html(self, current_suspect=None):
        if current_suspect is None:
            current_suspect = self.state.current_suspect
        character = self.characters[current_suspect]
        filtered_messages = [msg for msg in self.conversation_history if msg.get('suspect') == current_suspect]

        mobile_css = """
        <style>
        @media (max-width: 768px) {
            .chat-container { height: 450px !important; padding: 12px !important; }
            .chat-messages { padding-right: 20px !important; }
            .user-message, .ai-message { max-width: 85% !important; font-size: 15px !important; }
        }
        @media (max-width: 480px) {
            .chat-container { height: 400px !important; padding: 10px !important; }
            .user-message, .ai-message { max-width: 90% !important; font-size: 14px !important; }
        }
        </style>
        """

        html_content = f"""
        {mobile_css}
        <div class="chat-container" style="{Styles.CYBERPUNK_BG}; padding: 0; font-family: 'Courier New', monospace; height: 520px; overflow: hidden; border-radius: 12px; {Styles.NEON_BORDER}; box-shadow: {Styles.NEON_SHADOW}; position: relative;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: #001f3f; z-index: 1;"></div>
            <div class="character-image" style="position: absolute; right: 15px; bottom: 15px; width: 240px; height: 300px; background: url('{character.image_url}') top center / cover no-repeat; border: 3px solid #00ffff; border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 255, 255, 0.5); z-index: 2;"></div>
            <div class="chat-messages" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0, 20, 40, 0.3); padding: 20px; padding-right: 20px; overflow-y: auto; z-index: 3; box-sizing: border-box;">
        """

        if not filtered_messages:
            html_content += f"""
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; width: 100%;">
                    <div style="text-align: center; color: #88ddff; font-size: 16px; opacity: 0.9; text-shadow: 0 2px 4px rgba(0,0,0,0.5); padding: 20px; background: rgba(0, 255, 255, 0.1); border-radius: 10px; border: 1px solid rgba(0, 255, 255, 0.3); backdrop-filter: blur(5px); max-width: 400px;">
                        🔍 {character.name}와의 심문을 시작하세요
                        <div style="font-size: 14px; color: #aabbcc; margin-top: 10px; line-height: 1.4;">질문을 입력하거나 아래 빠른 질문 버튼을 사용하세요</div>
                    </div>
                </div>
            """
        else:
            for msg in filtered_messages:
                if msg['role'] == 'user':
                    html_content += f"""
                        <div style="display: flex; justify-content: flex-end; margin-bottom: 16px; width: 100%;">
                            <div style="display: flex; flex-direction: column; align-items: flex-end; max-width: 75%; width: fit-content;">
                                <div class="user-message" style="background: linear-gradient(145deg, #0088ff, #0066cc); color: white; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.5; word-wrap: break-word; box-shadow: 0 4px 12px rgba(0, 136, 255, 0.4); border: 1px solid #00aaff; font-weight: 500;">
                                    🕵️ {msg['content']}
                                </div>
                                <div style="font-size: 11px; color: #99ddff; margin-top: 6px; opacity: 0.8;">{msg['time']}</div>
                            </div>
                        </div>
                    """
                else:
                    html_content += f"""
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 16px; width: 100%;">
                            <div style="display: flex; flex-direction: column; max-width: 75%; width: fit-content;">
                                <div style="font-size: 12px; color: #88eeff; margin-bottom: 6px; font-weight: bold; opacity: 0.9;">🤖 {character.name}</div>
                                <div class="ai-message" style="background: linear-gradient(145deg, rgba(60, 60, 60, 0.96), rgba(50, 50, 50, 0.96)); color: #ffffff; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.5; word-wrap: break-word; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25); margin-bottom: 6px; border: 1px solid #00ffff; font-weight: 500;">
                                    {msg['content']}
                                </div>
                                <div style="font-size: 11px; color: #aaddff; opacity: 0.8;">{msg['time']}</div>
                            </div>
                        </div>
                    """

        html_content += f"""
            </div>
        </div>
        """
        return html_content

    def interrogate_suspect(self, message, suspect_name):
        if not message.strip():
            return self.create_chat_html(), ""

        self.state.current_suspect = suspect_name
        current_time = self.get_current_time()

        user_msg = {'role': 'user', 'content': message, 'time': current_time, 'timestamp': datetime.now().isoformat(), 'suspect': suspect_name, 'style': '직접적'}
        self.conversation_history.append(user_msg)
        self.state.interrogation_count[suspect_name] += 1

        try:
            character = self.characters[suspect_name]
            full_prompt = f"{character.system_prompt}\n\n상황: 플레이어가 심문을 진행하고 있습니다. 자연스러운 구어체로 대화하되, 방어적이고 경계하는 반응을 보이세요. 규칙: 2-3문장으로 자연스럽게 답변. 실제 사람이 말하는 것처럼 구어체를 사용하세요. 심문 {self.state.interrogation_count[suspect_name]}회차."

            api_messages = [{"role": "system", "content": full_prompt}]
            suspect_history = [msg for msg in self.conversation_history if msg.get('suspect') == suspect_name][-4:]

            for hist_msg in suspect_history[:-1]:
                role = "user" if hist_msg['role'] == 'user' else "assistant"
                api_messages.append({"role": role, "content": hist_msg['content']})

            api_messages.append({"role": "user", "content": message})

            response = client.chat.completions.create(model="gpt-4-turbo-preview", messages=api_messages, temperature=0.9, max_tokens=120, presence_penalty=0.3, frequency_penalty=0.3)

            ai_response = response.choices[0].message.content
            trust_change = self.calculate_trust_change(message, ai_response)
            self.state.trust_levels[suspect_name] = max(0, min(100, self.state.trust_levels[suspect_name] + trust_change))
            self.check_evidence_discovery(message, ai_response)

            time.sleep(random.uniform(1.0, 2.0))

            ai_msg = {'role': 'assistant', 'content': ai_response, 'time': self.get_current_time(), 'timestamp': datetime.now().isoformat(), 'suspect': suspect_name, 'trust_change': trust_change}
            self.conversation_history.append(ai_msg)
            self.update_game_progress()

        except Exception as e:
            error_msg = {'role': 'assistant', 'content': f"[시스템 오류] 연결이 불안정합니다... ({str(e)})", 'time': self.get_current_time(), 'timestamp': datetime.now().isoformat(), 'suspect': suspect_name, 'error': True}
            self.conversation_history.append(error_msg)

        return self.create_chat_html(), ""

    def get_interrogation_info_html(self, suspect_name):
        character = self.characters[suspect_name]
        return f"""
        <div style="{Styles.panel()}; margin-bottom: 15px; text-align: center;">
            <div style="color: #ff9999; font-weight: bold; margin-bottom: 12px; font-size: 15px;">🔍 INTERROGATION ROOM</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                <div style="padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px;">
                    <div style="color: #ffee88; font-weight: 600; font-size: 12px;">SUSPECT</div>
                    <div style="color: #ffffff; font-size: 13px; margin-top: 2px;">{character.name}</div>
                </div>
                <div style="padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px;">
                    <div style="color: #ffee88; font-weight: 600; font-size: 12px;">TRUST</div>
                    <div style="color: #88ff88; font-size: 13px; margin-top: 2px; font-weight: bold;">{self.state.trust_levels[suspect_name]}%</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div style="padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px;">
                    <div style="color: #ffee88; font-weight: 600; font-size: 12px;">QUESTIONS</div>
                    <div style="color: #88ddff; font-size: 13px; margin-top: 2px; font-weight: bold;">{self.state.interrogation_count[suspect_name]}</div>
                </div>
                <div style="padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px;">
                    <div style="color: #ffee88; font-weight: 600; font-size: 12px;">EVIDENCE</div>
                    <div style="color: #ff88dd; font-size: 13px; margin-top: 2px; font-weight: bold;">{len(self.state.evidence_collected)}/8</div>
                </div>
            </div>
        </div>
        """

    def get_report_status_html(self):
        total_questions = sum(self.state.interrogation_count.values())
        evidence_count = len(self.state.evidence_collected)
        can_submit = self.update_game_progress()

        if can_submit:
            return f"""
            <div style="background: linear-gradient(145deg, rgba(0,255,0,0.2), rgba(0,200,0,0.3)); color: #00ff00; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 2px solid #00ff00; font-size: 14px; text-align: center; box-shadow: 0 4px 16px rgba(0, 255, 0, 0.3);">
                <div style="font-weight: bold; margin-bottom: 5px;">✅ 보고서 제출 가능!</div>
                <div style="font-size: 12px; opacity: 0.9;">증거: {evidence_count}/8 | 질문: {total_questions}회</div>
            </div>
            """
        else:
            return f"""
            <div style="background: linear-gradient(145deg, rgba(255,165,0,0.2), rgba(255,140,0,0.3)); color: #ffaa00; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 2px solid #ffaa00; font-size: 14px; text-align: center; box-shadow: 0 4px 16px rgba(255, 165, 0, 0.3);">
                <div style="font-weight: bold; margin-bottom: 5px;">📊 추가 수사 필요</div>
                <div style="font-size: 12px; opacity: 0.9; line-height: 1.3;">증거 {evidence_count}/2 | 질문 {total_questions}/4<br><span style="font-size: 11px;">(최소: 증거 2개, 질문 4회)</span></div>
            </div>
            """

    def get_character_info_html(self, suspect_name):
        character = self.characters[suspect_name]
        return f"""
        <div style="background: linear-gradient(145deg, rgba(20, 30, 50, 0.9), rgba(30, 40, 70, 0.9)); color: #ffffff; padding: 18px; border-radius: 12px; border: 2px solid #66aaff; font-family: 'Courier New', monospace; backdrop-filter: blur(8px); box-shadow: 0 8px 32px rgba(102, 170, 255, 0.3); margin-bottom: 15px;">
            <h4 style="color: #ffdd88; margin-bottom: 12px; font-size: 16px; text-shadow: 0 1px 3px rgba(0,0,0,0.3); text-align: center; border-bottom: 1px solid rgba(255, 221, 136, 0.3); padding-bottom: 8px;">👤 SUSPECT PROFILE</h4>
            <div style="text-align: center; margin-bottom: 15px;">
                <div style="color: #88ddff; font-size: 15px; font-weight: bold; margin-bottom: 8px;">{character.name}</div>
                <div style="color: #ccddee; font-size: 14px; line-height: 1.5; text-align: left; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">{character.description}</div>
            </div>
            <!-- PROGRESS 박스를 SUSPECT PROFILE 안에 추가 -->
            <div style="text-align: center; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 2px solid #44ff44;">
                <div style="color: #88ff88; font-size: 12px; font-weight: 600; margin-bottom: 3px;">PROGRESS</div>
                <div style="color: #ffffff; font-size: 14px; font-weight: bold;">{self.state.player_progress}%</div>
            </div>
        </div>
        """

    def get_case_summary(self):
        total_questions = sum(self.state.interrogation_count.values())
        evidence_count = len(self.state.evidence_collected)
        trust_analysis = []
        for suspect_id, trust in self.state.trust_levels.items():
            questions = self.state.interrogation_count[suspect_id]
            status = "높은 신뢰" if trust >= 70 else "보통 신뢰" if trust >= 40 else "낮은 신뢰"
            trust_analysis.append(f"• {self.characters[suspect_id].name}: {trust}% ({questions}회 심문, {status})")

        evidence_list = self.state.evidence_collected if self.state.evidence_collected else ["아직 수집된 증거가 없습니다."]

        return f"""
🔍 CASE INVESTIGATION SUMMARY

📊 전체 수사 진행도: {self.state.player_progress}%

📋 심문 현황:
• 총 질문 수: {total_questions}회
• 수집된 증거: {evidence_count}개

👥 용의자별 신뢰도:
{chr(10).join(trust_analysis)}

🔍 수집된 증거:
{chr(10).join([f"• {evidence}" for evidence in evidence_list])}

📈 수사 상태:
{'✅ 최종 보고서 제출 가능' if self.state.case_solved else '🔄 추가 수사 필요'}

☕ 사건의 핵심:
- Elena가 전날 밤 커피캡슐에 청산가리 주입
- IRIS-01이 Elena의 명령으로 독이 든 커피를 Alexander에게 제공
- Alexander는 평소 모닝커피 루틴 중 사망

💡 수사 팁:
- 각 용의자를 골고루 심문하세요
- 커피, 캡슐, 주사기 관련 키워드에 주목하세요
- Elena의 심야 활동과 IRIS-01의 작업 로그를 확인하세요
        """

    def reset_game(self):
        self.state = GameState()
        self.conversation_history = []
        self.experiment_data = {'conversations': [], 'analysis_results': {}, 'player_behavior': {}}
        return True

    def get_report_modal_html(self):
        total_questions = sum(self.state.interrogation_count.values())
        evidence_count = len(self.state.evidence_collected)

        if evidence_count < 2 or total_questions < 4:
            return f"""
            <div style="background: linear-gradient(145deg, rgba(255,0,0,0.2), rgba(200,0,0,0.3)); color: #ff6666; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #ff6666; font-family: 'Courier New', monospace; box-shadow: 0 8px 32px rgba(255, 102, 102, 0.3);">
                <h3 style="color: #ff6666; margin-bottom: 18px; font-size: 20px;">⚠️ 보고서 제출 불가</h3>
                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <p style="margin-bottom: 12px; font-size: 15px;">더 많은 증거와 심문이 필요합니다:</p>
                    <div style="margin: 8px 0; font-size: 14px;">🔍 수집된 증거: {evidence_count}/2 (최소 2개 필요)</div>
                    <div style="margin: 8px 0; font-size: 14px;">❓ 심문 횟수: {total_questions}/4 (최소 4회 필요)</div>
                </div>
                <p style="margin-top: 15px; font-size: 14px; color: #ffaaaa;">계속 수사를 진행해주세요!</p>
            </div>
            """, gr.update(visible=True)

        return self.generate_report_modal_content(), gr.update(visible=True)

    def generate_report_modal_content(self):
        questions_html = ""
        for question in self.case_questions:
            options_html = "".join([
                f'<label style="display: block; margin: 8px 0; cursor: pointer; color: #ffffff; font-size: 14px; padding: 10px; border-radius: 8px; background: linear-gradient(145deg, rgba(0,0,0,0.3), rgba(20,20,40,0.3)); border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; text-align: left;"><input type="radio" name="question_{question["id"]}" value="{option}" style="margin-right: 12px; accent-color: #00ffff; transform: scale(1.2);"> {option}</label>'
                for option in question["options"]
            ])

            questions_html += f"""
            <div style="margin-bottom: 25px; padding: 20px; background: linear-gradient(145deg, rgba(0,0,0,0.4), rgba(20,30,50,0.4)); border-radius: 12px; border: 2px solid #00ffff; box-shadow: 0 4px 16px rgba(0, 255, 255, 0.2);">
                <h4 style="color: #00ffff; margin-bottom: 15px; font-size: 16px; text-align: center; text-shadow: 0 1px 3px rgba(0,0,0,0.5);">{question["question"]}</h4>
                <div style="margin: 0;">{options_html}</div>
            </div>
            """

        script_data = {
            'questions': [q["id"] for q in self.case_questions],
            'correct_answers': {q["id"]: q["correct_answer"] for q in self.case_questions},
            'question_data': {q["id"]: {"question": q["question"], "hint": q["hint"]} for q in self.case_questions}
        }

        return f"""
        <style>
        @media (max-width: 768px) {{
            .modal-container {{ padding: 15px !important; max-width: 95% !important; max-height: 90vh !important; }}
            .modal-buttons {{ flex-direction: column !important; gap: 10px !important; }}
        }}
        </style>
        
        <div id="reportModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; display: none; backdrop-filter: blur(8px);">
            <div class="modal-container" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: linear-gradient(145deg, #0a0a0a, #1a1a2e); border: 3px solid #00ffff; border-radius: 15px; padding: 30px; max-width: 750px; width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 0 50px rgba(0, 255, 255, 0.4); font-family: 'Courier New', monospace;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 10px;">🔍 최종 수사 보고서 🔍</h2>
                    <p style="color: #ffdd88; font-size: 15px;">수집한 증거를 바탕으로 사건의 진실을 밝혀내세요</p>
                </div>
                <form id="reportForm">{questions_html}
                    <div class="modal-buttons" style="display: flex; justify-content: center; gap: 15px; margin-top: 30px;">
                        <button type="button" onclick="submitReport()" style="background: linear-gradient(145deg, #ff6b6b, #ee5a52); color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);">🎯 수사 완료!</button>
                        <button type="button" onclick="closeModal()" style="background: linear-gradient(145deg, #666, #555); color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 16px; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.4);">취소</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="resultModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1001; display: none;">
            <div class="modal-container" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: linear-gradient(145deg, #0a0a0a, #1a1a2e); border: 3px solid #FFD700; border-radius: 15px; padding: 30px; max-width: 800px; width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 0 50px rgba(255, 215, 0, 0.4); font-family: 'Courier New', monospace;">
                <div id="resultContent"></div>
                <div style="text-align: center; margin-top: 30px;">
                    <button type="button" onclick="closeResultModal()" style="background: linear-gradient(145deg, #00ffff, #0088cc); color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(0, 255, 255, 0.4);">🔍 계속 수사하기</button>
                </div>
            </div>
        </div>

        <script>
            const scriptData = {json.dumps(script_data, ensure_ascii=False)};
            function openReportModal() {{ document.getElementById('reportModal').style.display = 'block'; }}
            function closeModal() {{ document.getElementById('reportModal').style.display = 'none'; }}
            function closeResultModal() {{ document.getElementById('resultModal').style.display = 'none'; }}
            function submitReport() {{
                const answers = {{}};
                scriptData.questions.forEach(questionId => {{
                    const selected = document.querySelector(`input[name="question_${{questionId}}"]:checked`);
                    answers[questionId] = selected ? selected.value : "";
                }});
                let correctCount = 0;
                let resultsHtml = "";
                scriptData.questions.forEach(questionId => {{
                    const userAnswer = answers[questionId] || "미답변";
                    const correctAnswer = scriptData.correct_answers[questionId];
                    const isCorrect = userAnswer === correctAnswer;
                    if (isCorrect) correctCount++;
                    const statusIcon = isCorrect ? "✅" : "❌";
                    const answerColor = isCorrect ? "#88ff88" : "#ff8888";
                    resultsHtml += `<div style="margin-bottom: 15px; padding: 15px; background: linear-gradient(145deg, rgba(0,0,0,0.3), rgba(20,30,50,0.3)); border-radius: 10px; border-left: 4px solid ${{answerColor}};"><div style="color: #ffffff; margin-bottom: 8px; font-size: 15px;"><strong>${{scriptData.question_data[questionId].question}}</strong></div><div style="margin-bottom: 6px; font-size: 14px;"><span style="color: #ffdd88;">당신의 답:</span> <span style="color: ${{answerColor}}; font-weight: bold;">${{userAnswer}} ${{statusIcon}}</span></div><div style="margin-bottom: 6px; font-size: 14px;"><span style="color: #ffdd88;">정답:</span> <span style="color: #88ff88; font-weight: bold;">${{correctAnswer}}</span></div>${{!isCorrect ? `<div style="color: #aabbcc; font-size: 13px; font-style: italic; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 5px; margin-top: 8px;">💡 ${{scriptData.question_data[questionId].hint}}</div>` : ""}}</div>`;
                }});
                const totalQuestions = scriptData.questions.length;
                const scorePercentage = (correctCount / totalQuestions) * 100;
                let grade, gradeColor, finalMessage;
                if (scorePercentage >= 90) {{
                    grade = "S급 탐정"; gradeColor = "#FFD700";
                    finalMessage = "완벽한 추리력! 당신은 진정한 사이버펑크 탐정입니다! 🕵️‍♂️⭐";
                }} else if (scorePercentage >= 80) {{
                    grade = "A급 탐정"; gradeColor = "#00FF00";
                    finalMessage = "훌륭한 수사 실력! 대부분의 진실을 밝혀냈습니다! 🔍✨";
                }} else if (scorePercentage >= 70) {{
                    grade = "B급 탐정"; gradeColor = "#00AAFF";
                    finalMessage = "좋은 추리! 몇 가지 단서를 놓쳤지만 사건을 해결했습니다! 🎯";
                }} else {{
                    grade = "수습 탐정"; gradeColor = "#FF6666";
                    finalMessage = "더 많은 증거 수집이 필요했습니다. 다시 도전해보세요! 💪";
                }}
                const finalHtml = `<div style="text-align: center; margin-bottom: 25px;"><h2 style="color: ${{gradeColor}}; font-size: 26px; margin-bottom: 10px;">🏆 사건 수사 완료! 🏆</h2><div style="color: ${{gradeColor}}; font-size: 20px; font-weight: bold; margin-bottom: 8px;">${{grade}}</div><div style="color: #ffffff; font-size: 16px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; display: inline-block;">정답률: ${{correctCount}}/${{totalQuestions}} (${{scorePercentage.toFixed(1)}}%)</div></div><div style="margin-bottom: 20px;"><h3 style="color: #00ffff; margin-bottom: 15px; font-size: 18px; text-align: center;">📋 수사 결과</h3>${{resultsHtml}}</div><div style="text-align: center; margin-top: 20px; padding: 18px; background: linear-gradient(145deg, rgba(0,255,255,0.1), rgba(0,200,255,0.1)); border-radius: 12px; border: 1px solid rgba(0,255,255,0.3);"><div style="color: #ffffff; font-size: 15px;">${{finalMessage}}</div></div>`;
                document.getElementById('resultContent').innerHTML = finalHtml;
                document.getElementById('reportModal').style.display = 'none';
                document.getElementById('resultModal').style.display = 'block';
            }}
            setTimeout(() => openReportModal(), 100);
        </script>
        """

# 게임 인스턴스 생성
game = CyberpunkGame()

# Gradio UI 함수들
def clear_game():
    game.reset_game()
    return (game.create_chat_html(), "", game.get_interrogation_info_html('Elena'), game.get_report_status_html())

def interrogate_and_update_info(message, suspect_name):
    chat_html, empty_input = game.interrogate_suspect(message, suspect_name)
    return (chat_html, empty_input, game.get_interrogation_info_html(suspect_name), game.get_report_status_html())

def update_character_info_and_display(suspect_name):
    game.state.current_suspect = suspect_name
    return (game.get_character_info_html(suspect_name), game.get_interrogation_info_html(suspect_name), game.create_chat_html(suspect_name))

# Gradio 인터페이스 생성
with gr.Blocks(title="사이버펑크 추리 게임", theme=gr.themes.Monochrome()) as demo:
    gr.HTML("""
    <style>
    @media (max-width: 768px) {
        .gradio-container { padding: 10px !important; }
        .gr-button { font-size: 14px !important; padding: 12px 16px !important; margin: 4px !important; }
    }
    .gr-button:hover { transform: translateY(-1px) !important; }
    </style>
    """)
    
    gr.HTML(f"""
    <div style="text-align: center; background: linear-gradient(90deg, #000, #0a0a0a, #000); color: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 20px; {Styles.NEON_BORDER}; box-shadow: {Styles.NEON_SHADOW};">
        <h1 style="font-family: 'Courier New', monospace; font-size: clamp(22px, 5vw, 30px); margin-bottom: 10px; color: #ffffff;">🔍 CYBERPUNK MURDER INVESTIGATION 🤖</h1>
        <p style="font-size: clamp(13px, 3vw, 15px); color: #ffd93d;">근미래 사이버펑크 도시에서 발생한 Alexander 독살 사건을 해결하세요</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            chat_display = gr.HTML(value=game.create_chat_html(), label="심문실")
            interrogation_info = gr.HTML(value=game.get_interrogation_info_html('Elena'), label="")

            with gr.Row():
                message_input = gr.Textbox(placeholder="용의자에게 질문을 입력하세요...", label="", scale=4, container=False, lines=1)
                send_btn = gr.Button("🔍 질문", variant="primary", scale=1, size="lg")

            gr.HTML("""
            <div style="margin: 15px 0 10px 0; padding: 15px; 
                       background: linear-gradient(145deg, rgba(20, 20, 20, 0.95), rgba(10, 10, 10, 0.95)); 
                       border-radius: 10px; text-align: center; border: 2px solid rgba(255, 255, 255, 0.1);
                       box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3); backdrop-filter: blur(5px);
                       display: flex; align-items: center; justify-content: center; min-height: 50px;">
                <div style="color: #ffdd88; font-weight: bold; font-size: 16px; text-shadow: 0 1px 3px rgba(0,0,0,0.5);">💭 빠른 질문 버튼</div>
            </div>
            """)
            
            with gr.Column():
                with gr.Row():
                    quick1 = gr.Button("🕐 사건 당일 어디에 있었나?", size="sm", variant="secondary")
                    quick2 = gr.Button("💔 Alexander와 어떤 관계였나?", size="sm", variant="secondary")
                with gr.Row():
                    quick3 = gr.Button("👁️ 의심스러운 행동을 본 적 있나?", size="sm", variant="secondary")
                    quick4 = gr.Button("🤐 숨기고 있는 게 있다면 말해달라", size="sm", variant="secondary")

        with gr.Column(scale=1):
            gr.HTML("""
            <div style="background: linear-gradient(145deg, rgba(20, 20, 20, 0.95), rgba(10, 10, 10, 0.95)); 
                       padding: 20px; border-radius: 12px; margin-bottom: 15px;
                       border: 2px solid rgba(255, 255, 255, 0.1); text-align: center;
                       box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3); backdrop-filter: blur(5px);
                       display: flex; align-items: center; justify-content: center; min-height: 60px;">
                <h3 style="color: #ffffff; margin: 0; font-size: 18px; font-weight: bold; 
                          text-shadow: 0 1px 3px rgba(0,0,0,0.5);">🤖 용의자 선택</h3>
            </div>
            """)

            suspect_choice = gr.Radio(
                choices=[("👩 Elena (아내)", "Elena"), ("🤖 IRIS-01 (가정부 로봇)", "IRIS-01"), ("👨‍🔬 Dr. Chen (개발자)", "Dr. Chen"), ("🖥️ ZEN (보안 AI)", "ZEN")],
                value="Elena", label="심문할 용의자", info="각 용의자를 선택하면 해당 캐릭터와 대화할 수 있습니다"
            )

            with gr.Group():
                character_info = gr.HTML(value=game.get_character_info_html('Elena'), label="")

            gr.HTML("""
            <div style="background: linear-gradient(145deg, rgba(20, 20, 20, 0.95), rgba(10, 10, 10, 0.95)); 
                       padding: 20px; border-radius: 12px; margin-bottom: 15px;
                       border: 2px solid rgba(255, 255, 255, 0.1); text-align: center;
                       box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3); backdrop-filter: blur(5px);
                       display: flex; align-items: center; justify-content: center; min-height: 60px;">
                <h3 style="color: #ffffff; margin: 0; font-size: 18px; font-weight: bold; 
                          text-shadow: 0 1px 3px rgba(0,0,0,0.5);">🎯 최종 보고서</h3>
            </div>
            """)

            submit_report_btn = gr.Button("📋 최종 보고서 제출", variant="primary", size="lg", visible=True)
            report_status = gr.HTML(value=game.get_report_status_html(), label="")
            modal_container = gr.HTML(value="", label="", visible=False)

            gr.HTML("""
            <div style="background: linear-gradient(145deg, rgba(20, 20, 20, 0.95), rgba(10, 10, 10, 0.95)); 
                       padding: 20px; border-radius: 12px; margin-bottom: 15px;
                       border: 2px solid rgba(255, 255, 255, 0.1); text-align: center;
                       box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3); backdrop-filter: blur(5px);
                       display: flex; align-items: center; justify-content: center; min-height: 60px;">
                <h3 style="color: #ffffff; margin: 0; font-size: 18px; font-weight: bold; 
                          text-shadow: 0 1px 3px rgba(0,0,0,0.5);">📊 수사 도구</h3>
            </div>
            """)

            with gr.Column():
                case_summary_btn = gr.Button("📋 수사 현황 보기", variant="secondary", size="lg")
                case_summary_output = gr.Textbox(label="📊 수사 리포트", lines=14, interactive=False, visible=False)
                clear_btn = gr.Button("🔄 수사 초기화", variant="stop", size="lg")

    # 이벤트 핸들러
    send_btn.click(interrogate_and_update_info, inputs=[message_input, suspect_choice], outputs=[chat_display, message_input, interrogation_info, report_status])
    message_input.submit(interrogate_and_update_info, inputs=[message_input, suspect_choice], outputs=[chat_display, message_input, interrogation_info, report_status])

    def send_quick_question(question, suspect):
        return interrogate_and_update_info(question, suspect)

    quick1.click(lambda s: send_quick_question("사건 당일 어디에 있었나요?", s), inputs=[suspect_choice], outputs=[chat_display, message_input, interrogation_info, report_status])
    quick2.click(lambda s: send_quick_question("Alexander와 어떤 관계였나요?", s), inputs=[suspect_choice], outputs=[chat_display, message_input, interrogation_info, report_status])
    quick3.click(lambda s: send_quick_question("의심스러운 행동을 본 적 있나요?", s), inputs=[suspect_choice], outputs=[chat_display, message_input, interrogation_info, report_status])
    quick4.click(lambda s: send_quick_question("숨기고 있는 게 있다면 말해달라", s), inputs=[suspect_choice], outputs=[chat_display, message_input, interrogation_info, report_status])

    suspect_choice.change(update_character_info_and_display, inputs=[suspect_choice], outputs=[character_info, interrogation_info, chat_display])
    submit_report_btn.click(game.get_report_modal_html, outputs=[modal_container, modal_container])
    case_summary_btn.click(lambda: (game.get_case_summary(), gr.update(visible=True)), outputs=[case_summary_output, case_summary_output])
    clear_btn.click(clear_game, outputs=[chat_display, message_input, interrogation_info, report_status])

# 인터페이스 실행
if __name__ == "__main__":
    demo.launch(share=True, debug=True)
