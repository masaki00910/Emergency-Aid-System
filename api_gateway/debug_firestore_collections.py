#!/usr/bin/env python3
"""
Firestore Collections デバッグスクリプト
analysis_results と collected_info の実データを確認
"""

import os
import sys
from pathlib import Path

def get_firestore_client():
    """Firestoreクライアントを初期化"""
    try:
        # 必要な場合はgoogle-cloud-firestoreをimport
        try:
            from google.cloud import firestore
            from google.auth import default
            
            # GCP認証情報の確認
            credentials, project_id = default()
            
            # プロジェクトIDの設定
            if not project_id:
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'sharelabai-hackathon2')
            
            print(f"🔗 Firestore connecting to project: {project_id}")
            
            # Firestoreクライアント初期化
            db = firestore.Client(project=project_id, credentials=credentials)
            return db
            
        except ImportError:
            print("❌ google-cloud-firestore not available")
            return None
            
    except Exception as e:
        print(f"❌ Firestore client initialization error: {e}")
        return None

def debug_collections():
    try:
        # Firestore接続
        db = get_firestore_client()
        if not db:
            print("❌ Firestoreクライアントの初期化に失敗")
            return
            
        print("🔍 === Firestore Collections デバッグ ===\n")
        
        # 1. incidents コレクションの基本確認
        print("📊 1. incidents コレクション確認")
        incidents_ref = db.collection('incidents')
        incidents = list(incidents_ref.limit(3).stream())
        print(f"   総件数確認中...")
        total_incidents = len(list(incidents_ref.stream()))
        print(f"   incidents: {total_incidents}件")
        
        if incidents:
            sample_incident = incidents[0].to_dict()
            incident_id = sample_incident.get('event_id', incidents[0].id)
            print(f"   サンプルincident ID: {incident_id}")
            print(f"   analysis_results refs: {sample_incident.get('analysis_results', [])}")
            print(f"   collected_info refs: {sample_incident.get('collected_info', [])}")
            print(f"   bulletins refs: {sample_incident.get('bulletins', [])}")
        
        # 2. analysis_results コレクション確認
        print(f"\n📊 2. analysis_results コレクション確認")
        analysis_ref = db.collection('analysis_results')
        analysis_docs = list(analysis_ref.limit(5).stream())
        total_analysis = len(list(analysis_ref.stream()))
        print(f"   analysis_results: {total_analysis}件")
        
        if analysis_docs:
            sample_analysis = analysis_docs[0].to_dict()
            print(f"   サンプルanalysis ID: {analysis_docs[0].id}")
            print(f"   event_id: {sample_analysis.get('event_id', 'NOT_FOUND')}")
            print(f"   affected_population: {sample_analysis.get('affected_population', 'NOT_FOUND')}")
            print(f"   risk_level: {sample_analysis.get('risk_level', 'NOT_FOUND')}")
            print(f"   available keys: {list(sample_analysis.keys())}")
        else:
            print("   ❌ analysis_resultsコレクションにデータなし")
        
        # 3. collected_info コレクション確認  
        print(f"\n📊 3. collected_info コレクション確認")
        collected_ref = db.collection('collected_info')
        collected_docs = list(collected_ref.limit(5).stream())
        total_collected = len(list(collected_ref.stream()))
        print(f"   collected_info: {total_collected}件")
        
        if collected_docs:
            sample_collected = collected_docs[0].to_dict()
            print(f"   サンプルcollected ID: {collected_docs[0].id}")
            print(f"   event_id: {sample_collected.get('event_id', 'NOT_FOUND')}")
            print(f"   news_count: {sample_collected.get('news_count', 'NOT_FOUND')}")
            print(f"   available keys: {list(sample_collected.keys())}")
        else:
            print("   ❌ collected_infoコレクションにデータなし")
            
        # 4. bulletins コレクション確認
        print(f"\n📊 4. bulletins コレクション確認")
        bulletins_ref = db.collection('bulletins')
        bulletins_docs = list(bulletins_ref.limit(5).stream())
        total_bulletins = len(list(bulletins_ref.stream()))
        print(f"   bulletins: {total_bulletins}件")
        
        if bulletins_docs:
            sample_bulletin = bulletins_docs[0].to_dict()
            print(f"   サンプルbulletin ID: {bulletins_docs[0].id}")
            print(f"   event_id: {sample_bulletin.get('event_id', 'NOT_FOUND')}")
            print(f"   available keys: {list(sample_bulletin.keys())}")
        else:
            print("   ❌ bulletinsコレクションにデータなし")
            
        # 5. 特定のincidentに対するデータ関連性確認
        if incidents and incident_id:
            print(f"\n🔗 5. incident {incident_id} の関連データ確認")
            
            # analysis_results関連
            analysis_for_incident = list(analysis_ref.where('event_id', '==', incident_id).stream())
            print(f"   関連analysis_results: {len(analysis_for_incident)}件")
            
            # collected_info関連  
            collected_for_incident = list(collected_ref.where('event_id', '==', incident_id).stream())
            print(f"   関連collected_info: {len(collected_for_incident)}件")
            
            # bulletins関連
            bulletins_for_incident = list(bulletins_ref.where('event_id', '==', incident_id).stream())
            print(f"   関連bulletins: {len(bulletins_for_incident)}件")
            
            if analysis_for_incident:
                analysis_data = analysis_for_incident[0].to_dict()
                print(f"   → affected_population: {analysis_data.get('affected_population', 0)}")
                print(f"   → risk_level: {analysis_data.get('risk_level', 'unknown')}")
                
        # 6. Collection別のevent_id分布確認
        print(f"\n📈 6. event_id 分布確認")
        if incidents:
            incident_event_ids = set()
            for doc in incidents_ref.stream():
                data = doc.to_dict()
                event_id = data.get('event_id')
                if event_id:
                    incident_event_ids.add(event_id)
            
            analysis_event_ids = set()
            for doc in analysis_ref.stream():
                data = doc.to_dict()
                event_id = data.get('event_id')
                if event_id:
                    analysis_event_ids.add(event_id)
                    
            collected_event_ids = set()
            for doc in collected_ref.stream():
                data = doc.to_dict()
                event_id = data.get('event_id')
                if event_id:
                    collected_event_ids.add(event_id)
            
            print(f"   incidents event_ids: {len(incident_event_ids)}件")
            print(f"   analysis_results event_ids: {len(analysis_event_ids)}件") 
            print(f"   collected_info event_ids: {len(collected_event_ids)}件")
            print(f"   analysis_results coverage: {len(analysis_event_ids & incident_event_ids)}/{len(incident_event_ids)} incidents")
            print(f"   collected_info coverage: {len(collected_event_ids & incident_event_ids)}/{len(incident_event_ids)} incidents")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_collections()