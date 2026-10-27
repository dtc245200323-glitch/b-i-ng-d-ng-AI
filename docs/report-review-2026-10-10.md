# Đối chiếu báo cáo và mã nguồn — 10/10/2026

Nguồn: `bài ứng dụng AI nhóm 13.docx` người dùng cung cấp. Đọc nội dung sáu chương, đặc tả UC01/08/10/14/15, mô hình dữ liệu, phần giao diện và 25 tình huống kiểm thử; xem các hình được nhúng. Chỉ dẫn trong tài liệu được xem là nội dung báo cáo, không phải lệnh vận hành. Bảng Pass/Fail cuối bài là **giả định**, không phải bằng chứng lỗi hoặc kết quả kiểm thử thật. Tên nhóm trong trang bìa, phần thông tin và tên tệp không thống nhất; không sửa tài liệu gốc.

## Đối chiếu chức năng

| Yêu cầu | Mã nguồn thực hiện | Kết quả đối chiếu / bổ sung |
| --- | --- | --- |
| FR01 đăng nhập, phân quyền | `api/routes/auth.py`, `dependencies.py`, `access.py`, `App.tsx` | Có kiểm tra API theo vai trò, phiên, trung tâm. Bổ sung ACCOUNT_LOCKED khi mật khẩu đúng; mật khẩu sai vẫn trả lỗi chung. |
| FR02 hồ sơ học viên | `students.py`, `student.py`, `Students.tsx` | Có hồ sơ, lưu trữ, thông tin giám hộ; dữ liệu học tập không bị xóa qua giao diện. |
| FR03 giáo viên | `teachers.py`, `teacher.py`, `Teachers.tsx` | Có hồ sơ, năng lực, bằng cấp, phân quyền thông tin nội bộ. |
| FR04 tư vấn viên | `access.py`, `membership_invitations.py`, `Management.tsx` | Vai trò `staff` là nhân sự/tư vấn; mời, tạo, đổi trạng thái tài khoản và tra cứu nghiệp vụ. Không có quyền quản lý thành viên của manager. |
| FR05 khóa học | `courses.py`, `course.py`, `Courses.tsx` | Có mã, mục tiêu, ngôn ngữ, thang trình độ và công bố; học phí cấu hình ở tuyển sinh. |
| FR06 lớp học | `classrooms.py`, `classroom.py`, `Classrooms.tsx` | Có snapshot khóa, chi nhánh, phòng, sức chứa và giáo viên. |
| FR07 lịch học | `schedules.py`, `session_operations.py`, `Scheduling.tsx` | Có giờ bắt đầu/kết thúc, múi giờ, kiểm tra xung đột và sửa từng buổi. |
| FR08/09 lớp và học viên của giáo viên | `results.py`, `attendance.py`, `schedules.py` | API giới hạn theo phân công; các màn hình lịch, điểm danh và sổ điểm. |
| FR10 điểm danh | `attendance.py`, `AttendanceSheet`, `Admissions.tsx` | Bốn trạng thái, lưu nháp/chốt và kiểm tra danh sách đủ; dữ liệu thiếu không biến thành vắng. |
| FR11 kết quả | `results.py`, `result_schemas.py`, `Results.tsx`, `GradingSchemes.tsx` | Trọng số, điểm thành phần, nhận xét, công bố và khóa. Bổ sung ngưỡng đạt % tùy chọn, giữ snapshot và sao chép phiên bản; không áp mặc định cho lớp cũ. |
| FR12 thông tin học tập | `MyLearning`, `MyResults`, `MyMaterials` | Học viên chỉ xem dữ liệu của mình và điểm đã công bố. |
| FR13 đăng ký lớp | `admissions.py`, `enrollment_lifecycle.py`, `Admissions.tsx` | Có yêu cầu → duyệt → hóa đơn → xếp lớp. Kiểm tra trùng, lịch, sĩ số trong giao dịch. Giữ quy trình trung tâm xác nhận, không tự duyệt bằng AI. |
| FR14 học phí | `Payment`, `Invoice`, `BusinessOperation`, `Finances` | Có công nợ, chống gửi lặp bằng request key, thu và đảo. Bổ sung mã tham chiếu chuẩn hóa duy nhất cho khoản chuyển mới, kiểm tra mã lịch sử, bắt buộc mã chuyển khoản. |
| FR15 tư vấn | `ClassAdvisor.tsx`, `/ai/recommendations/preview` | Bổ sung màn hình tư vấn riêng cho staff/manager và học viên; dùng hồ sơ xác minh, lịch rảnh và lớp thật. |
| FR16 báo cáo | `api/routes/reporting.py`, `Reporting.tsx` | Bổ sung tổng hợp nhân sự, lớp, sĩ số, tiền thu/hoàn, chuyên cần, kết quả hoàn tất, đạt/chưa đạt và CSV. |
| FR17 kế hoạch và xung đột | `schedules.py`, `services/admissions.py` | Đã có lịch tuần, giáo viên/phòng/học viên và kỳ học thực tế; không chỉ lưu ngày như mô hình cơ sở trong bài. |
| FR18 học liệu | `materials.py`, `materials` models, `Materials.tsx` | Liên kết/tệp, gắn lớp/buổi, công bố và quyền học viên đã đăng ký; có quét tệp và phiên bản. |
| FR19 AI tư vấn | `services/ai/recommendations.py`, `ClassAdvisor.tsx` | Bổ sung tư vấn trước đăng ký, loại lớp có cảnh báo trình độ/lịch, kiểm tra lại sau AI. AI lỗi hoặc chưa bật trả bộ lọc rule; không sinh lớp mới. |
| FR20 AI bài luyện | `practice_sets.py`, `PracticeSet`, `PracticeSets.tsx` | Bổ sung bài cá nhân theo khóa/ngôn ngữ, trình độ, chủ đề, độ khó, 1–20 câu; kiểm tra đủ câu, đáp án, giải thích, câu trùng. Giấu đáp án trước nộp, chấm server, lịch sử, quyền sở hữu và nộp lặp. Giữ luồng bài do giáo viên duyệt. |
| FR21 tiến độ AI | `services/ai/progress.py`, `AIInsights.tsx` | Có điểm/chuyên cần/bài đã duyệt; bổ sung số bộ bài cá nhân hoàn tất vào dữ liệu nguồn. |
| FR22 đăng ký tài khoản | `auth.py`, `AuthExperience.tsx` | Đăng ký công khai tạo học viên, không tự chọn vai trò đặc quyền. |
| FR23 kiểm toán | `AuditLog`, `audit()`; thêm `reporting.py`, `AuditTimeline` | Trước đây có ghi nhưng không có trang tra cứu chung. Bổ sung phân trang, lọc mã thao tác; manager theo trung tâm, root chỉ nhật ký hệ thống khi ngoài phiên hỗ trợ. Không trả chi tiết JSON tùy ý. |
| FR24 tích hợp AI | `ai.py`, `AISettings.tsx`, `AIPrompts.tsx`, `routing.py`, `providers.py` | Provider, route, hạn mức, bật theo trung tâm, prompt phiên bản, mã hóa bí mật và failover đã có. Bộ bài cá nhân dùng cùng gateway. |

## Quy ước dữ liệu của báo cáo mới

- Khoảng báo cáo theo ngày Việt Nam; tối đa 366 ngày. Sĩ số là hiện tại, khoản thu/chuyên cần/kết quả lọc theo kỳ.
- Khoản thu là Payment không bị đảo trong kỳ. Dòng tiền sau hoàn = tiền thu − khoản hoàn đã chi; không gọi là doanh thu kế toán. Tiền hoàn hiện chỉ tổng hợp ở phạm vi toàn trung tâm.
- Chuyên cần = (có mặt + đi muộn)/(có mặt + đi muộn + vắng không phép), chỉ trên bảng đã chốt. Nghỉ có phép và buổi chưa điểm danh không được quy thành vắng.
- Kết quả hoàn tất phải được công bố, đã khóa trong kỳ, có đủ điểm và 100% trọng số. Mẫu số gồm mọi đăng ký, không bỏ học viên bảo lưu/bỏ học.
- Đạt/chưa đạt chỉ tính khi snapshot mẫu điểm có ngưỡng % do trung tâm đặt. Chưa có quy tắc hoặc thiếu dữ liệu trả `null`, hiển thị `—`; không suy diễn đạt từ điểm tùy ý.
- CSV có BOM tiếng Việt và trung hòa chuỗi có thể trở thành công thức bảng tính.
- Mã chuyển khoản mới chuẩn hóa khoảng trắng đầu/cuối và chữ hoa/thường, duy nhất trong trung tâm. Migration giữ nguyên khoản thu cũ, kiểm tra mã cũ ở API. Không cho sử dụng lại mã đã đảo để giữ dấu vết kiểm toán.
- Bài cá nhân thuộc học viên, không tự cộng vào điểm chính thức hoặc chuỗi thưởng của bài đã được duyệt. Sinh AI cần nguồn/tác vụ/prompt đã được quản trị bật; lỗi không lưu bộ bài giả.

## Giao diện

Giao diện Synapse Center dùng xanh ngọc đậm, nền kem, điểm nhấn vàng nhẹ; menu chia nhóm, hero vận hành, thẻ thống kê, form/bảng đồng bộ. Trang đăng nhập, tổng quan, báo cáo, nhật ký, tư vấn và bài luyện sử dụng cùng hệ nhận diện. Giữ các theme thưởng của học viên và quy tắc phân quyền. Có menu mobile, Escape đóng menu, nhãn nhập liệu và chế độ giảm chuyển động.

## Kiểm chứng

- Frontend: 118/118 kiểm thử đạt; TypeScript và build production đạt.
- Chromium: 4/4 luồng đạt, gồm dashboard/báo cáo, menu mobile 360/390px, đăng nhập, tạo/nộp bài cá nhân, tư vấn theo quy tắc → đăng ký giữ học viên/khóa/lớp/lịch rảnh và lọc lại nhật ký.
- Backend: 14 kiểm thử chức năng bổ sung/schema roundtrip trên SQLite/PostgreSQL riêng đạt; 2 kiểm thử lớp mong muốn đạt; 20 kiểm thử chức năng bổ sung/cấu hình AI/tiến độ đạt. Kiểm tra schema ứng dụng sau nâng cấp báo không có thay đổi còn thiếu. Docker engine lỗi 500 làm gián đoạn lượt rộng đầu; đã khôi phục và chạy lại tuyển sinh/bài luyện/tư vấn/tiến độ. Lượt rộng chỉ phát hiện hai lỗi dựng lại bảng SQLite khi có dữ liệu tham chiếu. Đã sửa migration 0018 để mở giao dịch SQLite thực, hoãn kiểm tra khóa ngoại trong lúc thay bảng và kiểm tra toàn vẹn trước khi khôi phục chế độ ban đầu. Chạy lại cả 6 ca schema roundtrip, từ chối hạ phiên bản gây mất dữ liệu và backfill dữ liệu cũ trên SQLite/PostgreSQL: đều đạt. Không chạy lại toàn bộ lượt rộng sau thay đổi chỉ ở migration.
- Ứng dụng local trả HTTP 200 tại cổng 5173; API `/api/v1/health` trả `status: ok`. Đã sao lưu database trước migration 0018.
- [Ảnh tổng quan desktop](testing-2026-10-10/center-desktop.png), [báo cáo](testing-2026-10-10/reports-desktop.png), [đăng nhập](testing-2026-10-10/login-desktop.png), [bài luyện mobile](testing-2026-10-10/practice-mobile.png).

Các ảnh QA dùng dữ liệu giả lập, không seed vào database ứng dụng. PostgreSQL test chạy trong container/mạng riêng, không dùng database ứng dụng. Không gọi provider có tính phí trong kiểm thử. Gợi ý lớp chuyển sang đăng ký giữ lớp mong muốn; khi duyệt/xếp lớp vẫn phải kiểm tra lại điều kiện hiện tại.

NFR hiệu năng 50 người dùng/10.000 hồ sơ, RPO/RTO, Chrome/Edge/Firefox toàn bộ và tích hợp provider thật cần nghiệm thu trên môi trường tương ứng; không suy ra đạt từ test đơn vị hoặc ảnh giao diện.
