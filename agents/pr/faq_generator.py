import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Dict

sys.path.append(r"C:\ACN\My_EmergencyAidSystem\Emergency-Aid-System")
from agents.common.base_agent import BaseAgent
from shared.models.disaster import AgentTask, AgentResult, TaskStatus
from shared.utils.vertex_ai_client import vertex_ai_client
from google.cloud import firestore

db = firestore.Client()
logger = logging.getLogger(__name__)

class FAQGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("faq_generator")

    async def process(self, task: AgentTask) -> AgentResult:
        try:
            await self.log_agent_action("start_faq_generation", {"task_id": task.task_id})

            input_text = task.payload.get("content", "")
            if not input_text:
                raise ValueError("No input content provided for FAQ generation.")

            # キーワード抽出
            keywords = await vertex_ai_client.extract_keywords(content=input_text)
            logger.info(f"Extracted keywords: {keywords}")

            # FAQ生成
            faqs = []
            for keyword in keywords:
                faq_item = await vertex_ai_client.generate_faq_dynamic(keyword=keyword, context=input_text)
                # faq_item が dict か list かを確認してリストに追加
                if isinstance(faq_item, list):
                    faqs.extend(faq_item)
                else:
                    faqs.append(faq_item)

            # 重複質問を削除＆件数制御（最大3件）
            unique_faqs = []
            seen_questions = set()
            for faq_item in faqs:
                question = faq_item.get("question")
                if question and question not in seen_questions:
                    unique_faqs.append(faq_item)
                    seen_questions.add(question)
                if len(unique_faqs) >= 3:  # 最大3件
                    break
            faqs = unique_faqs

            result_data = {"keywords": keywords, "faqs": faqs}
            await self.log_agent_action("faq_generation_completed", result_data)

            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.DONE,
                result=result_data,
                updated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.FAILED,
                result={},
                updated_at=datetime.utcnow(),
                errors=[str(e)]
            )

# --- 単体テスト ---
if __name__ == "__main__":
    dummy_task = AgentTask(
        task_id="test-faq-001",
        event_id="dummy-event-001",
        agent="faq_generator",
        payload={"content": "大雨による洪水や土砂災害の危険があります。"},
        created_at=datetime.utcnow()
    )

    agent = FAQGeneratorAgent()

    async def run_test():
        result = await agent.process(dummy_task)
        faqs = result.result.get("faqs", [])

        print("=== FAQ生成結果 ===")
        for faq in faqs:
            print("Q:", faq["question"])
            print("A:", faq["answer"])

        # --- 重要 ---
        # FAQ生成直後に、FAQ と（空の）user_interactions を一つのドキュメントに保存する
        # (event_id をドキュメントIDとして使う)
        save_faq_and_chats(dummy_task.event_id, faqs)

        # --- ユーザとの対話 ---
        while True:
            user_input = input("\n質問してください (終了するには 'exit'): ")
            if user_input.lower() in ["exit", "quit"]:
                break

            # Vertex AI に FAQ を参照させて回答を生成する想定
            answer = await vertex_ai_client.answer_with_faq(faqs, user_input)
            print("AI:", answer)

            # Firestore に追加（同一ドキュメントの user_interactions 配列に追加）
            add_user_interaction(dummy_task.event_id, user_input, answer)

        
    def save_faq_and_chats(event_id: str, faqs: list, user_interactions: list | None = None):
        """
        FAQ と初期のユーザ対話（通常は空）を 1 ドキュメントにまとめて保存する。
        doc id は event_id を使う（重複保存は上書き）。
        """
        doc_ref = db.collection("faq_chat_logs").document(event_id)
        data = {
            "faqs": faqs,
            "user_interactions": user_interactions or [],  # 初期は空配列
            "created_at": datetime.utcnow().isoformat()
        }
        doc_ref.set(data)
        print(f"FAQとチャット（初期）を保存しました: {doc_ref.id}")


    def add_user_interaction(event_id: str, user_input: str, answer: str):
        """
        既存ドキュメントにユーザの質問＆回答を追加する。
        ドキュメントが存在しない場合は新規作成する（faqsは空のまま）。
        """
        doc_ref = db.collection("faq_chat_logs").document(event_id)
        new_entry = {
            "user_input": user_input,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            # 既存配列に追加
            doc_ref.update({"user_interactions": firestore.ArrayUnion([new_entry])})
            print(f"ユーザ質問を追加しました: {doc_ref.id}")
        except Exception as e:
            # ドキュメントが無い等で update が失敗した場合は作成する
            doc_ref.set({
                "faqs": [],
                "user_interactions": [new_entry],
                "created_at": datetime.utcnow().isoformat()
            })
            print(f"ドキュメントが無かったため新規作成して追加しました: {doc_ref.id}")
        
    asyncio.run(run_test())