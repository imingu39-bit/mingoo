import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# 1. 슈파베이스 설정 (주소 끝을 .co로 깔끔하게 정리했습니다)
SUPABASE_URL = "https://cizmkuclzlegcbqvmwgc.supabase.co" 
SUPABASE_KEY = "sb_publishable_dTuHbPdeAHe9bFJVBvV-0g_oeD_Afi8"

# 슈파베이스 연결 엔진
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SK시그넷 전국 고장신고", layout="wide")
st.title("🚧 SK시그넷 전국 고장 신고 시스템")

tab1, tab2 = st.tabs(["📝 고장 신고 접수", "📋 실시간 신고 내역"])

# --- [탭 1: 고장 신고] ---
with tab1:
    st.info("현장 관리자가 사용하는 신고 화면입니다.")
    with st.form("reporting_form", clear_on_submit=True):
        reporter = st.text_input("신고인 성함")
        charger_id = st.text_input("충전기 ID (예: MAC001)")
        category = st.selectbox("고장 유형", ["캐노피 파손", "충전불가", "커넥터 파손", "디스플레이 고장", "기타"])
        details = st.text_area("상세 내용 설명")
        
        uploaded_file = st.file_uploader("현장 사진 업로드", type=['png', 'jpg', 'jpeg'])
        
        submit = st.form_submit_button("신고 데이터 전송")

        if submit:
            if not reporter or not charger_id:
                st.warning("⚠️ 성함과 충전기 ID를 입력해주세요.")
            else:
                with st.spinner("서버에 저장 중..."):
                    try:
                        img_url = ""
                        # 사진이 있으면 Storage에 업로드 (버킷 이름: maintenance_photos)
                        if uploaded_file:
                            file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                            supabase.storage.from_("maintenance_photos").upload(file_name, uploaded_file.getvalue())
                            img_url = supabase.storage.from_("maintenance_photos").get_public_url(file_name)

                        # DB 저장 (테이블 이름: maintenance_report)
                        data = {
                            "reporter": reporter,
                            "charger_id": charger_id,
                            "category": category,
                            "details": details,
                            "image_url": img_url,
                            "status": "접수완료"
                        }
                        supabase.table("maintenance_report").insert(data).execute()
                        st.success("✅ 전국 통합 서버로 신고가 정상 접수되었습니다!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"⚠️ 연결 오류 발생: {e}")
                        st.info("슈파베이스의 'maintenance_report' 테이블이 생성되어 있는지 확인해주세요.")

# --- [탭 2: 전체 내역 확인] ---
with tab2:
    st.subheader("📋 실시간 전국 접수 현황")
    try:
        # DB에서 최신순으로 데이터 가져오기
        response = supabase.table("maintenance_report").select("*").order("created_at", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("현재 접수된 내역이 없습니다.")
    except Exception as e:
        st.error(f"데이터 조회 오류: {e}")
        
