import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import re

# 1. Supabase 설정 (기존 정보 유지)
SUPABASE_URL = "https://cizmkuclzlegcbqvmwgc.supabase.co" 
SUPABASE_KEY = "sb_publishable_dTuHbPdeAHe9bFJVBvV-0g_oeD_Afi8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SK시그넷 통합 유지보수", layout="wide")
st.title("🚧 SK시그넷 전국 고장 신고 및 점검 관리 시스템")

tab1, tab2 = st.tabs(["📝 서비스/점검 접수", "📋 관리자용 내역 관리"])

# --- [탭 1: 서비스/점검 접수 - 현장 담당자용] ---
with tab1:
    st.info("현장 안전관리자 및 점검 담당자가 입력하는 화면입니다. 사진(JPG) 및 점검 결과서(PDF) 업로드가 가능합니다.")
    with st.form("reporting_form", clear_on_submit=True):
        company_name = st.text_input("회사명")  # 신고인 성함에서 회사명으로 변경
        charger_id = st.text_input("충전기 ID")
        # 고장 유형 리스트 수정: 디스플레이 고장 -> 정기점검
        category = st.selectbox("접수 유형", ["정기점검", "충전불가", "커넥터 파손", "캐노피 파손", "기타"])
        details = st.text_area("상세 내용(점검 특이사항 등)")
        
        uploaded_file = st.file_uploader("현장 사진 또는 점검 보고서 업로드", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        submit = st.form_submit_button("데이터 전송")

        if submit:
            if not company_name or not charger_id:
                st.error("회사명과 충전기 ID는 필수 입력 사항입니다.")
            else:
                with st.spinner("데이터 전송 중..."):
                    file_url = ""
                    if uploaded_file:
                        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                        
                        try:
                            supabase.storage.from_("maintenance_photos").upload(file_name, uploaded_file.getvalue())
                            file_url = supabase.storage.from_("maintenance_photos").get_public_url(file_name)
                        except Exception as e:
                            st.error(f"파일 업로드 중 오류 발생: {e}")

                    # DB 데이터 삽입 (reporter 컬럼을 회사명 저장 용도로 사용)
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
                        st.success(f"✅ {company_name}의 접수 건이 '접수중' 상태로 정상 등록되었습니다.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"DB 저장 중 오류 발생: {e}")

# --- [탭 2: 실시간 내역 관리 - 관리자용] ---
with tab2:
    st.subheader("📋 실시간 접수 현황 및 처리 상태")
    
    try:
        response = supabase.table("maintenance_report").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            for record in response.data:
                # 상태별 이모지 배지
                status_emoji = {"접수중": "🔴", "접수완료": "🟠", "수리중": "🟡", "수리완료": "🟢"}.get(record['status'], "⚪")
                
                # 리스트 제목에 회사명 노출
                with st.expander(f"{status_emoji} [{record['status']}] {record['charger_id']} ({record['reporter']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**🏢 접수 회사:** {record['reporter']}")
                        st.write(f"**🛠️ 접수 유형:** {record['category']}")
                        st.write(f"**📝 상세 내용:** {record['details']}")
                        st.write(f"**⏰ 등록 시간:** {record['created_at']}")
                        
                        if record['image_url']:
                            is_pdf = record['image_url'].lower().endswith('.pdf')
                            if is_pdf:
                                st.write("---")
                                st.write("📄 **첨부된 보고서(PDF)**")
                                st.link_button("PDF 보고서 열기", record['image_url'])
                            else:
                                st.write("---")
                                st.write("📸 **현장 사진 미리보기**")
                                st.image(record['image_url'], width=400)
                    
                    with col2:
                        st.write("**⚙️ 진행 상태 변경**")
                        new_status = st.selectbox("상태 선택", ["접수중", "접수완료", "수리중", "수리완료"], 
                                                 index=["접수중", "접수완료", "수리중", "수리완료"].index(record['status']),
                                                 key=f"sel_{record['id']}")
                        
                        if st.button("업데이트", key=f"btn_{record['id']}"):
                            supabase.table("maintenance_report").update({"status": new_status}).eq("id", record["id"]).execute()
                            st.success("상태 변경 완료")
                            st.rerun()
        else:
            st.info("현재 접수된 내역이 없습니다.")
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        
        
