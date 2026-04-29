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
    st.info("💡 현장 담당자님, 아래 정보를 입력해 주세요. (사진 및 **PDF 보고서** 업로드 가능)")
    with st.form("reporting_form", clear_on_submit=True):
        # 1. '신고인 성함' -> '회사명'으로 라벨 변경
        company_name = st.text_input("🏢 회사명", placeholder="예: SK시그넷 서비스팀") 
        
        # 2. 충전기 ID 입력
        charger_id = st.text_input("⚡ 충전기 ID", placeholder="예: MAC0000XXXX")
        
        # 3. 고장 유형 -> 정기점검 포함
        category = st.selectbox("🛠️ 접수 유형 선택", ["정기점검", "충전불가", "커넥터 파손", "캐노피 파손", "기타"])
        
        # 4. 상세 내용
        details = st.text_area("📝 상세 내용 (점검 특이사항 또는 고장 현상)")
        
        # 5. PDF 포함 안내 문구 수정
        uploaded_file = st.file_uploader("📂 현장 사진 또는 점검 보고서(PDF) 업로드", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        submit = st.form_submit_button("🚀 데이터 전송하기")

        if submit:
            if not company_name or not charger_id:
                st.error("⚠️ 회사명과 충전기 ID는 필수 입력 사항입니다.")
            else:
                with st.spinner("데이터를 Supabase로 전송 중..."):
                    file_url = ""
                    if uploaded_file:
                        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                        
                        try:
                            supabase.storage.from_("maintenance_photos").upload(file_name, uploaded_file.getvalue())
                            file_url = supabase.storage.from_("maintenance_photos").get_public_url(file_name)
                        except Exception as e:
                            st.error(f"파일 업로드 중 오류 발생: {e}")

                    # DB 저장 (필드명은 기존 DB 구조에 맞춤)
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
                        st.success(f"✅ {company_name}의 {category} 접수 건이 정상 등록되었습니다.")
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
                status_emoji = {"접수중": "🔴", "접수완료": "🟠", "수리중": "🟡", "수리완료": "🟢"}.get(record['status'], "⚪")
                
                # 리스트 제목 부분 UI 개선
                with st.expander(f"{status_emoji} [{record['status']}] {record['charger_id']} | 접수처: {record['reporter']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**🏢 접수 회사:** {record['reporter']}")
                        st.write(f"**🛠️ 접수 유형:** {record['category']}")
                        st.write(f"**📝 상세 내용:** {record['details']}")
                        st.write(f"**⏰ 등록 시간:** {record['created_at']}")
                        
                        if record['image_url']:
                            # 파일이 PDF인지 확인
                            is_pdf = record['image_url'].lower().endswith('.pdf')
                            if is_pdf:
                                st.write("---")
                                st.info("📄 **첨부된 PDF 보고서가 있습니다.**")
                                st.link_button("📥 PDF 보고서 확인 및 다운로드", record['image_url'])
                            else:
                                st.write("---")
                                st.write("📸 **현장 사진**")
                                st.image(record['image_url'], width=500)
                    
                    with col2:
                        st.write("**⚙️ 처리 상태 변경**")
                        new_status = st.selectbox("상태 변경", ["접수중", "접수완료", "수리중", "수리완료"], 
                                                 index=["접수중", "접수완료", "수리중", "수리완료"].index(record['status']),
                                                 key=f"sel_{record['id']}")
                        
                        if st.button("업데이트", key=f"btn_{record['id']}"):
                            supabase.table("maintenance_report").update({"status": new_status}).eq("id", record["id"]).execute()
                            st.success("상태가 변경되었습니다.")
                            st.rerun()
        else:
            st.info("현재 접수된 내역이 없습니다.")
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        
        
