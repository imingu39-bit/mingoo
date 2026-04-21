import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# 1. 다른 컴퓨터에서 보내주신 슈파베이스 정보 (책임님 정보로 자동 셋팅)
SUPABASE_URL = "https://your-project-id.supabase.co" # 보내주신 URL 넣으세요
SUPABASE_KEY = "your-anon-key"                      # 보내주신 API Key 넣으세요
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 앱 설정
st.set_page_config(page_title="SK시그넷 전국 통합 유지보수", layout="wide")
st.title("🚧 SK시그넷 고장 신고 시스템")

# 탭 구성
tab1, tab2 = st.tabs(["📝 고장 신고", "📊 전체 내역 확인"])

# --- [탭 1: 고장 신고] ---
with tab1:
    st.info("현장 안전관리자분들은 고장 부위 사진과 내용을 입력해 주세요.")
    with st.form("reporting_form", clear_on_submit=True):
        reporter = st.text_input("신고인 성함")
        charger_id = st.text_input("충전기 ID (예: MAC001)")
        category = st.selectbox("고장 유형", ["캐노피 파손", "전기차 충전불가", "커넥터 파손", "기타"])
        details = st.text_area("상세 내용")
        
        # 사진 업로드 기능
        uploaded_file = st.file_uploader("현장 사진 촬영/업로드", type=['png', 'jpg', 'jpeg'])
        
        submit = st.form_submit_button("전국 서버로 신고 접수")

        if submit:
            if not reporter or not charger_id:
                st.error("⚠️ 성함과 충전기 ID는 필수입니다.")
            else:
                with st.spinner("전국 서버로 데이터를 전송 중입니다..."):
                    img_url = ""
                    # 사진이 있을 경우 슈파베이스 Storage에 저장
                    if uploaded_file:
                        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                        # 'maintenance_photos' 버킷에 업로드
                        supabase.storage.from_("maintenance_photos").upload(file_name, uploaded_file.getvalue())
                        img_url = supabase.storage.from_("maintenance_photos").get_public_url(file_name)

                    # 슈파베이스 DB(Table)에 데이터 저장
                    data = {
                        "reporter": reporter,
                        "charger_id": charger_id,
                        "category": category,
                        "details": details,
                        "image_url": img_url,
                        "status": "접수완료"
                    }
                    supabase.table("maintenance_reports").insert(data).execute()
                    
                    st.success("✅ 전국 통합 서버로 신고가 정상 접수되었습니다!")
                    st.balloons()

# --- [탭 2: 전체 내역 확인] ---
with tab2:
    st.subheader("📋 실시간 전국 접수 현황")
    try:
        # 실시간 DB 조회
        response = supabase.table("maintenance_reports").select("*").order("created_at", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # 표에 사진 링크가 있으면 클릭 가능하게 표시
            st.dataframe(df, use_container_width=True)
        else:
            st.info("현재 접수된 전국 내역이 없습니다.")
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류 발생: {e}")
        