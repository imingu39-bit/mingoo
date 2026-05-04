import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import os

# 1. Supabase 설정 (보안을 위해 환경 변수 권장이나, 현재 코드 유지)
SUPABASE_URL = "https://cizmkuclzlegcbqvmwgc.supabase.co" 
SUPABASE_KEY = "sb_publishable_dTuHbPdeAHe9bFJVBvV-0g_oeD_Afi8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SK시그넷 통합 유지보수", layout="wide")
st.title("🚧 SK시그넷 전국 고장 신고 및 점검 시스템")

tab1, tab2 = st.tabs(["📝 서비스/점검 접수", "📋 관리자용 내역 관리"])

# --- [탭 1: 서비스/점검 접수] ---
with tab1:
    st.info("💡 현장 사진 또는 보고서를 업로드해 주세요. 파일명은 '날짜_시간'으로 자동 저장됩니다.")
    
    with st.form("reporting_form", clear_on_submit=True):
        company_name = st.text_input("🏢 회사명", placeholder="예: SK시그넷 서비스팀") 
        charger_id = st.text_input("⚡ 충전기 ID", placeholder="예: MAC0000XXXX")
        category = st.selectbox("🛠️ 접수 유형 선택", ["정기점검", "충전불가", "커넥터 파손", "캐노피 파손", "기타"])
        details = st.text_area("📝 상세 내용")
        uploaded_file = st.file_uploader("📂 현장 사진 또는 보고서(JPG, PDF 등)", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        submit = st.form_submit_button("🚀 데이터 전송하기")

        if submit:
            if not company_name or not charger_id:
                st.error("⚠️ 회사명과 충전기 ID는 필수 입력 사항입니다.")
            else:
                with st.spinner("데이터 및 파일 전송 중..."):
                    file_url = ""
                    
                    # --- 파일 업로드 로직 ---
                    if uploaded_file:
                        # 확장자 추출 (.jpg 등)
                        ext = os.path.splitext(uploaded_file.name)[1]
                        # 파일명을 현재 시간으로만 구성 (예: 20240522_143005.jpg)
                        safe_file_name = datetime.now().strftime('%Y%m%d_%H%M%S') + ext
                        
                        try:
                            # Supabase Storage 업로드
                            supabase.storage.from_("maintenance_photos").upload(
                                path=safe_file_name, 
                                file=uploaded_file.getvalue(),
                                file_options={"content-type": uploaded_file.type}
                            )
                            # 업로드된 파일의 공개 URL 생성
                            file_url = supabase.storage.from_("maintenance_photos").get_public_url(safe_file_name)
                        except Exception as e:
                            st.error(f"❌ 파일 업로드 실패: {e}")
                    
                    # --- DB 데이터 저장 로직 ---
                    data = {
                        "reporter": company_name, 
                        "charger_id": charger_id,
                        "category": category,
                        "details": details,
                        "image_url": file_url,
                        "status": "접수중"
                    }
                    
                    try:
                        supabase.table("maintenance_report").insert(data).execute()
                        st.success(f"✅ 접수가 완료되었습니다! (파일명: {safe_file_name if uploaded_file else '없음'})")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ DB 저장 실패: {e}")

# --- [탭 2: 내역 관리] ---
with tab2:
    st.subheader("📋 실시간 접수 현황")
    try:
        # 최신순으로 데이터 불러오기
        response = supabase.table("maintenance_report").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            for record in response.data:
                status_emoji = {"접수중": "🔴", "접수완료": "🟠", "수리중": "🟡", "수리완료": "🟢"}.get(record['status'], "⚪")
                
                with st.expander(f"{status_emoji} [{record['status']}] {record['charger_id']} | {record['reporter']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**🏢 접수 회사:** {record['reporter']}")
                        st.write(f"**🛠️ 유형:** {record['category']}")
                        st.write(f"**📝 내용:** {record['details']}")
                        
                        if record['image_url']:
                            if record['image_url'].lower().endswith('.pdf'):
                                st.info("📄 PDF 보고서가 첨부되었습니다.")
                                st.link_button("📥 PDF 열기", record['image_url'])
                            else:
                                st.image(record['image_url'], caption="현장 사진", use_column_width=True)
                        else:
                            st.caption("첨부된 파일이 없습니다.")
                            
                    with col2:
                        # 상태 변경 UI
                        current_status = record['status']
                        status_list = ["접수중", "접수완료", "수리중", "수리완료"]
                        
                        # 인덱스 방어 코드
                        try:
                            default_index = status_list.index(current_status)
                        except ValueError:
                            default_index = 0
                            
                        new_status = st.selectbox(
                            "상태 변경", 
                            status_list, 
                            index=default_index,
                            key=f"sel_{record['id']}"
                        )
                        
                        if st.button("상태 업데이트", key=f"btn_{record['id']}"):
                            supabase.table("maintenance_report").update({"status": new_status}).eq("id", record["id"]).execute()
                            st.toast(f"상태가 '{new_status}'(으)로 변경되었습니다!")
                            st.rerun()
        else:
            st.info("접수된 내역이 없습니다.")
            
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
