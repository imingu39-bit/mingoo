import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# 1. 설정
SUPABASE_URL = "https://cizmkuclzlegcbqvmwgc.supabase.co" 
SUPABASE_KEY = "sb_publishable_dTuHbPdeAHe9bFJVBvV-0g_oeD_Afi8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SK시그넷 통합 유지보수", layout="wide")
st.title("🚧 SK시그넷 전국 고장 신고 시스템")

tab1, tab2 = st.tabs(["📝 고장 신고 접수", "📋 관리자용 신고 내역"])

# --- [탭 1: 고장 신고 - 각 담당자용] ---
with tab1:
    st.info("현장 안전관리자가 입력하는 화면입니다.")
    with st.form("reporting_form", clear_on_submit=True):
        reporter = st.text_input("신고인 성함")
        charger_id = st.text_input("충전기 ID")
        category = st.selectbox("고장 유형", ["캐노피 파손", "충전불가", "커넥터 파손", "디스플레이 고장", "기타"])
        details = st.text_area("상세 내용")
        uploaded_file = st.file_uploader("현장 사진 업로드", type=['png', 'jpg', 'jpeg'])
        
        submit = st.form_submit_button("신고 데이터 전송")

        if submit:
            with st.spinner("데이터 전송 중..."):
                img_url = ""
                if uploaded_file:
                    file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                    supabase.storage.from_("maintenance_photos").upload(file_name, uploaded_file.getvalue())
                    img_url = supabase.storage.from_("maintenance_photos").get_public_url(file_name)

                # 최초 요청 시 status를 '접수중'으로 설정
                data = {
                    "reporter": reporter,
                    "charger_id": charger_id,
                    "category": category,
                    "details": details,
                    "image_url": img_url,
                    "status": "접수중"
                }
                supabase.table("maintenance_report").insert(data).execute()
                st.success("✅ '접수중' 상태로 정상 등록되었습니다.")
                st.balloons()

# --- [탭 2: 실시간 신고 내역 - 민구 책임님 전용] ---
with tab2:
    st.subheader("📋 실시간 접수 현황 및 상태 관리")
    
    # DB에서 데이터 가져오기
    response = supabase.table("maintenance_report").select("*").order("created_at", desc=True).execute()
    
    if response.data:
        for record in response.data:
            # 각 신고 내역을 한 칸씩(Expander) 보여줌
            with st.expander(f"[{record['status']}] {record['charger_id']} - {record['reporter']}님 신고"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**유형:** {record['category']}")
                    st.write(f"**내용:** {record['details']}")
                    st.write(f"**시간:** {record['created_at']}")
                    if record['image_url']:
                        st.image(record['image_url'], width=300)
                
                with col2:
                    # 관리자가 상태를 직접 변경하는 버튼
                    st.write("---")
                    new_status = st.selectbox("상태 변경", ["접수중", "접수완료", "수리중", "수리완료"], key=f"sel_{record['id']}")
                    if st.button("상태 업데이트", key=f"btn_{record['id']}"):
                        supabase.table("maintenance_report").update({"status": new_status}).eq("id", record["id"]).execute()
                        st.success(f"'{record['charger_id']}' 상태가 {new_status}(으)로 변경되었습니다!")
                        st.rerun() # 화면 즉시 새로고침
    else:
        st.info("현재 접수된 내역이 없습니다.")
        
        
