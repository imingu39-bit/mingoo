if submit:
            if not company_name or not charger_id:
                st.error("⚠️ 회사명과 충전기 ID는 필수 입력 사항입니다.")
            else:
                with st.spinner("데이터 전송 중..."):
                    file_url = ""
                    if uploaded_file:
                        # 1. 확장자만 추출 (예: .jpg, .pdf)
                        ext = os.path.splitext(uploaded_file.name)[1]
                        
                        # 2. 파일명을 '년월일_시분초'로만 생성 (예: 20260504_173045.jpg)
                        # 한글이나 회사명을 제외하여 에러 발생 가능성을 차단합니다.
                        safe_file_name = datetime.now().strftime('%Y%m%d_%H%M%S') + ext
                        
                        try:
                            # Supabase Storage 업로드
                            supabase.storage.from_("maintenance_photos").upload(
                                path=safe_file_name, 
                                file=uploaded_file.getvalue(),
                                file_options={"content-type": uploaded_file.type}
                            )
                            # 공용 URL 가져오기
                            file_url = supabase.storage.from_("maintenance_photos").get_public_url(safe_file_name)
                        except Exception as e:
                            st.error(f"❌ 파일 업로드 실패: {e}")

                    # DB 저장 부분 (동일)
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
                        st.success(f"✅ 접수 완료! (저장된 파일명: {safe_file_name})")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ DB 저장 실패: {e}")
