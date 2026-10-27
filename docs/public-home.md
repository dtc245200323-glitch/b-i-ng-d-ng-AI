# Trang chủ giới thiệu trung tâm

Khách chưa đăng nhập tại `/` thấy trang giới thiệu “Trung tâm ngoại ngữ”. Người đã có phiên đăng nhập vẫn vào dashboard theo vai trò. `/login` mở đăng nhập, `/register` mở đăng ký; các liên kết xác minh email, đặt lại mật khẩu và lời mời vẫn giữ luồng hiện có.

Trang chủ có menu cuộn tới giới thiệu, giảng viên/phương pháp, học viên, định hướng khóa học và tư vấn. Các CTA dẫn tới tài khoản thật; không tạo yêu cầu tư vấn giả hoặc hiển thị số liệu/thành tích giả. Nội dung khóa học là định hướng giới thiệu, chương trình và lịch cụ thể do trung tâm xác nhận.

Ảnh minh họa tải từ Unsplash và lưu local để không phụ thuộc kết nối tới dịch vụ ảnh khi xem trang:

- `frontend/public/images/center-learning.jpg`: https://images.unsplash.com/photo-1522071820081-009f0129c71c
- `frontend/public/images/center-community.jpg`: https://images.unsplash.com/photo-1523240795612-9a054b0db644

Kiểm tra: 118 kiểm thử frontend đạt, TypeScript/build đạt. Chromium kiểm tra homepage desktop 1440px và mobile/tablet 360/390/768px, ảnh tải được, không tràn ngang, menu cuộn/đóng và chuyển tới login/register đúng. Bốn luồng trình duyệt có sẵn cũng đạt; ca homepage chạy lại đạt sau khi sửa tên nhãn trong kiểm thử.

Ảnh QA: [desktop](testing-2026-10-10/homepage-desktop.png), [mobile](testing-2026-10-10/homepage-mobile.png).

## Chatbot tư vấn thường gặp

Nút “Tư vấn nhanh” ở góc dưới trang chủ mở chatbot gồm 5 nhóm: khóa học, học phí/thanh toán, lịch học, đăng ký và học thử/kiểm tra trình độ. Có thể bấm câu hỏi hoặc nhập câu hỏi; bộ nhận diện từ khóa hỗ trợ tiếng Việt có dấu/không dấu. Trả lời tự động theo nội dung FAQ, không gọi provider AI, không yêu cầu đăng nhập, không gửi nội dung hội thoại lên server. Hội thoại chỉ giữ trong bộ nhớ khi trang chủ đang mở. Câu ngoài phạm vi trả hướng dẫn rõ ràng; không bịa học phí, lịch lớp hoặc cam kết học thử.

TypeScript/build đạt. Kiểm thử Chromium đạt cả 5 câu trả lời, câu nhập không dấu, câu ngoài phạm vi, giữ hội thoại khi đóng/mở, phím Enter/Escape, trả focus về nút mở, panel mobile 360px và liên kết đăng ký. [Ảnh desktop](testing-2026-10-10/faq-desktop.png), [ảnh mobile](testing-2026-10-10/faq-mobile.png).
