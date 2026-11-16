import streamlit as st
from google import genai
import os

# Cấu hình trang web
st.set_page_config(
    page_title="BẮP AI VIDEO EDITOR",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 BẮP AI VIDEO EDITOR")
st.caption("Nền tảng tự động biên tập video TikTok Shop & Tạo kịch bản AI")

# Thanh bên (Sidebar) cấu hình API & Thông số
with st.sidebar:
    st.header("⚙️ Cấu hình hệ thống")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.secrets.get("GEMINI_API_KEY", "") if "GEMINI_API_KEY" in st.secrets else ""
    )
    
    st.divider()
    st.subheader("📐 Thông số xuất bản")
    aspect_ratio = st.selectbox("Tỷ lệ khung hình", ["9:16", "16:9", "1:1", "4:5"], index=0)
    resolution = st.selectbox("Độ phân giải", ["1080p", "720p", "2K", "4K"], index=0)
    style_version = st.radio("Phong cách dựng", ["CINEMATIC", "DYNAMIC", "NATURAL"])

# Giao diện chính chia 2 cột
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Tải lên Video & Sản phẩm")
    project_name = st.text_input("Tên dự án", placeholder="VD: Review Khay Đựng Trứng Thông Minh")
    uploaded_video = st.file_uploader("Chọn video gốc (MP4, MOV)", type=["mp4", "mov", "avi"])
    
    if uploaded_video:
        st.video(uploaded_video)
        st.success(f"Đã tải lên: {uploaded_video.name}")

with col2:
    st.subheader("2. Tạo kịch bản & Kế hoạch dựng AI")
    product_info = st.text_area(
        "Mô tả sản phẩm / Ý tưởng video",
        placeholder="Nhập điểm nổi bật của sản phẩm để AI lên kịch bản 30s chuẩn chuyển đổi...",
        height=120
    )
    
    if st.button("🚀 Phân tích & Tạo kịch bản AI", type="primary", use_container_width=True):
        if not api_key:
            st.error("Vui lòng nhập Gemini API Key ở thanh bên trái!")
        elif not product_info:
            st.warning("Vui lòng nhập mô tả sản phẩm hoặc ý tưởng video.")
        else:
            with st.spinner("AI đang phân tích và lên kịch bản..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = (
                        f"Đóng vai chuyên gia dựng video TikTok Shop. Hãy viết kịch bản voice-over đúng 30 giây "
                        f"(khoảng 75-85 từ tiếng Việt tự nhiên, cuốn hút) và chia cảnh chi tiết theo phong cách {style_version}, "
                        f"tỷ lệ khung hình {aspect_ratio} cho sản phẩm sau:\n{product_info}"
                    )
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=prompt
                    )
                    st.markdown("### 📝 Kế hoạch dựng & Lời thoại đề xuất")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Lỗi kết nối AI: {e}")
