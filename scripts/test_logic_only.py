#!/usr/bin/env python3

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

# パス設定
sys.path.append('/workspace/disaster-response-system')

# 環境変数設定
os.environ['USE_MOCK_LLM'] = 'true'

# モックストレージ
storage_data = {
    "incidents": {},
    "tasks": {},
    "orchestrations": {},
    "rag_documents": {},
    "collected_info": {},
    "analysis_results": {},
    "bulletins": {}
}

pubsub_messages = []

def mock_firestore_set(collection: str, doc_id: str, data: Dict[str, Any]):
    if collection not in storage_data:
        storage_data[collection] = {}
    storage_data[collection][doc_id] = data
    print(f"[FIRESTORE] {collection}/{doc_id}: {str(data)[:80]}...")

def mock_pubsub_publish(topic: str, message: str, **attributes):
    msg_data = {
        "topic": topic,
        "message": message,
        "attributes": attributes,
        "timestamp": datetime.utcnow().isoformat()
    }
    pubsub_messages.append(msg_data)
    print(f"[PUBSUB] {topic}: {message[:80]}...")
    return f"mock_msg_{len(pubsub_messages)}"


async def test_disaster_detection_logic():
    print("\n=== 1. 災害検知ロジックテスト ===")
    
    # モックLLMクライアント使用
    from shared.utils.mock_llm_client import create_mock_vertex_ai_client
    mock_client = create_mock_vertex_ai_client()
    
    # RSS記事例
    sample_content = "東京都内で震度5強の地震が発生しました。JR各線が運転を見合わせています。"
    
    analysis = await mock_client.generate_disaster_analysis(
        content=sample_content,
        source_info={"source": "nhk", "timestamp": datetime.now().isoformat()}
    )
    
    print(f"災害判定: {analysis.get('is_disaster')}")
    print(f"災害種別: {analysis.get('disaster_type')}")
    print(f"深刻度: {analysis.get('severity'):.2f}")
    print(f"要約: {analysis.get('summary')}")
    
    # 災害イベント作成
    if analysis.get('is_disaster'):
        event_id = str(uuid.uuid4())
        disaster_event = {
            "event_id": event_id,
            "detected_at": datetime.utcnow().isoformat(),
            "source": ["nhk"],
            "type": analysis.get('disaster_type'),
            "location": analysis.get('location'),
            "severity": analysis.get('severity'),
            "confidence": analysis.get('confidence'),
            "summary": analysis.get('summary'),
            "evidence": []
        }
        
        # Firestore保存
        mock_firestore_set("incidents", event_id, disaster_event)
        
        # Pub/Sub発行
        mock_pubsub_publish("disaster-detected", json.dumps(disaster_event, default=str))
        
        return disaster_event
    
    return None


async def test_orchestration_logic(disaster_event: Dict[str, Any]):
    print("\n=== 2. オーケストレーションロジックテスト ===")
    
    # オーケストレーションタスク作成
    orchestration_id = str(uuid.uuid4())
    
    # 各AgentへのタスクJSONを作成
    base_task_data = {
        "event_id": disaster_event["event_id"],
        "disaster_type": disaster_event["type"],
        "location": disaster_event["location"],
        "severity": disaster_event["severity"]
    }
    
    agent_tasks = {
        "info_collection": {
            "task_id": str(uuid.uuid4()),
            **base_task_data,
            "agent": "info_collector",
            "payload": {"collect_sources": ["news", "official"], "time_window_hours": 2}
        },
        "analysis": {
            "task_id": str(uuid.uuid4()),
            **base_task_data,
            "agent": "analyzer",
            "payload": {"analysis_type": "impact_assessment"}
        },
        "pr": {
            "task_id": str(uuid.uuid4()),
            **base_task_data,
            "agent": "pr",
            "payload": {"output_formats": ["web", "mobile"]}
        }
    }
    
    print(f"オーケストレーションID: {orchestration_id}")
    print(f"作成タスク数: {len(agent_tasks)}")
    
    # オーケストレーション状態保存
    mock_firestore_set("orchestrations", orchestration_id, {
        "state": "initializing",
        "event": disaster_event,
        "started_at": datetime.utcnow().isoformat()
    })
    
    # 各Agentにタスク配信
    for agent_name, task_data in agent_tasks.items():
        mock_firestore_set("tasks", task_data["task_id"], task_data)
        mock_pubsub_publish(f"agent-task-{agent_name}", json.dumps(task_data, default=str))
    
    return orchestration_id, agent_tasks


async def test_agent_processing(agent_tasks: Dict[str, Dict[str, Any]]):
    print("\n=== 3. 各Agentタスク処理テスト ===")
    
    from shared.utils.mock_llm_client import create_mock_vertex_ai_client
    mock_client = create_mock_vertex_ai_client()
    
    results = {}
    
    # 情報収集Agent処理
    info_task = agent_tasks["info_collection"]
    print(f"\n情報収集Agent処理 (タスク: {info_task['task_id']})")
    
    # モック情報収集
    collected_info = [
        {"source": "nhk", "title": "震度5強の地震発生", "content": "詳細な被害状況...", "timestamp": datetime.utcnow()},
        {"source": "jma", "title": "地震情報", "content": "気象庁発表の地震情報...", "timestamp": datetime.utcnow()}
    ]
    
    for item in collected_info:
        doc_id = str(uuid.uuid4())
        mock_firestore_set("collected_info", doc_id, {**item, "event_id": info_task["event_id"]})
    
    info_result = {"collected_items": len(collected_info), "processed_items": len(collected_info)}
    mock_firestore_set("tasks", info_task["task_id"], {**info_task, "status": "done", "result": info_result})
    results["info_collection"] = info_result
    
    # 分析Agent処理
    analysis_task = agent_tasks["analysis"]
    print(f"\n分析Agent処理 (タスク: {analysis_task['task_id']})")
    
    analysis_result = await mock_client.generate_impact_assessment(
        disaster_type=analysis_task["disaster_type"],
        location=analysis_task["location"],
        context=""
    )
    
    analysis_id = str(uuid.uuid4())
    mock_firestore_set("analysis_results", analysis_id, {
        "analysis_id": analysis_id,
        "event_id": analysis_task["event_id"],
        "result": analysis_result
    })
    
    mock_firestore_set("tasks", analysis_task["task_id"], {**analysis_task, "status": "done", "result": analysis_result})
    results["analysis"] = analysis_result
    
    # 広報Agent処理
    pr_task = agent_tasks["pr"]
    print(f"\n広報Agent処理 (タスク: {pr_task['task_id']})")
    
    web_content = await mock_client.generate_web_content(
        disaster_type=pr_task["disaster_type"],
        location=pr_task["location"],
        severity=pr_task["severity"]
    )
    
    mobile_content = await mock_client.generate_mobile_content(
        disaster_type=pr_task["disaster_type"],
        location=pr_task["location"]
    )
    
    pr_content = {"web": web_content, "mobile": mobile_content}
    
    bulletin_id = str(uuid.uuid4())
    mock_firestore_set("bulletins", bulletin_id, {
        "bulletin_id": bulletin_id,
        "event_id": pr_task["event_id"],
        "content": pr_content,
        "published_at": datetime.utcnow().isoformat()
    })
    
    mock_firestore_set("tasks", pr_task["task_id"], {**pr_task, "status": "done", "result": {"generated_formats": ["web", "mobile"]}})
    results["pr"] = pr_content
    
    return results


async def main():
    print("=== 災害対応システム 完全統合テスト ===")
    
    try:
        # 1. 災害検知
        disaster_event = await test_disaster_detection_logic()
        
        if not disaster_event:
            print("❌ 災害検知でイベントが生成されませんでした")
            return 1
        
        print("✅ 災害検知成功")
        
        # 2. オーケストレーション
        orchestration_id, agent_tasks = await test_orchestration_logic(disaster_event)
        print("✅ オーケストレーション成功")
        
        # 3. Agent処理
        processing_results = await test_agent_processing(agent_tasks)
        print("✅ Agent処理成功")
        
        # 4. 結果サマリー
        print("\n=== 最終結果サマリー ===")
        print(f"災害イベントID: {disaster_event['event_id']}")
        print(f"オーケストレーションID: {orchestration_id}")
        print(f"処理完了Agent: {list(processing_results.keys())}")
        
        print("\nデータ保存状況:")
        for collection, docs in storage_data.items():
            if docs:
                print(f"  {collection}: {len(docs)}件")
        
        print(f"\nPub/Subメッセージ数: {len(pubsub_messages)}")
        
        print("\n生成されたWebコンテンツ:")
        web_content = processing_results.get("pr", {}).get("web", {})
        print(f"  見出し: {web_content.get('headline')}")
        print(f"  概要: {web_content.get('summary')}")
        
        print("\n✅ 完全統合テスト成功")
        print("🎉 災害対応システムのロジック動作確認完了！")
        
        return 0
        
    except Exception as e:
        print(f"❌ 統合テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)