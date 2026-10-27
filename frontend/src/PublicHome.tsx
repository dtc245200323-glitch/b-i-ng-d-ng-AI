import { useState } from 'react'
import { Link } from 'react-router'
import { PublicFaqChat } from './PublicFaqChat'
import './public-home.css'

const programs = [
  { code: '01', tag: 'BẮT ĐẦU VỮNG VÀNG', name: 'Tiếng Anh nền tảng', description: 'Củng cố phát âm, từ vựng và ngữ pháp để tự tin bước vào hành trình học ngoại ngữ.', className: 'foundation' },
  { code: '02', tag: 'TỰ TIN KẾT NỐI', name: 'Tiếng Anh giao tiếp', description: 'Luyện nghe và nói qua những tình huống gần gũi trong học tập, công việc và cuộc sống.', className: 'communication' },
  { code: '03', tag: 'CHINH PHỤC MỤC TIÊU', name: 'Định hướng IELTS', description: 'Phát triển bốn kỹ năng, làm quen dạng bài và xây dựng kế hoạch luyện tập phù hợp.', className: 'ielts' },
]

export function PublicHome() {
  const [menuOpen, setMenuOpen] = useState(false)
  const closeMenu = () => setMenuOpen(false)
  return <div className="public-home">
    <a className="ph-skip" href="#home-content">Đến nội dung chính</a>
    <header className="ph-header"><div className="ph-nav-wrap">
      <Link className="ph-brand" to="/" aria-label="Trung tâm ngoại ngữ — trang chủ"><span className="ph-brand-mark" aria-hidden="true">N<span>✦</span></span><span>TRUNG TÂM<strong>NGOẠI NGỮ</strong></span></Link>
      <button type="button" className="ph-menu-toggle" aria-label={menuOpen ? 'Đóng menu trang chủ' : 'Mở menu trang chủ'} aria-expanded={menuOpen} aria-controls="public-navigation" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
      <nav id="public-navigation" className={menuOpen ? 'is-open' : ''} aria-label="Menu trang chủ" onKeyDown={e => { if (e.key === 'Escape') closeMenu() }}>
        <a href="#ve-chung-toi" onClick={closeMenu}>Về chúng tôi</a><a href="#giang-vien" onClick={closeMenu}>Giảng viên</a><a href="#hoc-vien" onClick={closeMenu}>Học viên</a><a href="#khoa-hoc" onClick={closeMenu}>Khóa học</a>
        <Link className="ph-login" to="/login" onClick={closeMenu}>Đăng nhập</Link>
      </nav><div className="ph-header-actions"><Link className="ph-button" to="/register">Đăng ký</Link></div>
    </div></header>
    <main id="home-content">
      <section className="ph-hero" aria-labelledby="home-title">
        <div className="ph-hero-pattern" aria-hidden="true" /><div className="ph-hero-inner">
          <div className="ph-hero-copy"><p className="ph-eyebrow">TRUNG TÂM NGOẠI NGỮ <span>·</span> LEARN. CONNECT. GROW.</p><p className="ph-hero-intro">Một ngôn ngữ mới.<br />Một thế giới rộng mở.</p>
            <h1 id="home-title"><span className="ph-title-top">HỌC NGOẠI NGỮ</span><span className="ph-title-main">TỰ TIN<br />VƯƠN XA<span className="ph-title-spark" aria-hidden="true">✦</span></span></h1>
            <p className="ph-hero-description">Bắt đầu từ trình độ của bạn. Tiến bộ bằng một lộ trình rõ ràng, sự đồng hành của giảng viên và những trải nghiệm học tập đầy cảm hứng.</p>
            <div className="ph-hero-actions"><a className="ph-button" href="#khoa-hoc">Khám phá khóa học <span aria-hidden="true">↗</span></a><a href="#tu-van" className="ph-text-link">Tìm lộ trình của bạn <span aria-hidden="true">→</span></a></div>
          </div>
          <div className="ph-hero-visual"><div className="ph-photo-frame"><img src="/images/center-learning.jpg" alt="Nhóm bạn cùng trao đổi và học tập trong không gian sáng tạo" fetchPriority="high" /><span className="ph-photo-label">CÙNG HỌC. CÙNG TIẾN BỘ.</span></div><div className="ph-floating-note"><span aria-hidden="true">✦</span><div>Hành trình của bạn<strong>Bắt đầu từ hôm nay.</strong></div></div><span className="ph-visual-caption">Ảnh minh họa không gian học tập</span></div>
        </div>
      </section>
      <section className="ph-feature-strip" aria-label="Trải nghiệm học tập"><a href="#ve-chung-toi" className="ph-feature"><span className="ph-feature-icon" aria-hidden="true">↗</span><div><p>HỌC CÓ ĐỊNH HƯỚNG</p><h2>Lộ trình phù hợp với bạn</h2><span>Từ nền tảng đến mục tiêu riêng.</span></div><span className="ph-feature-arrow" aria-hidden="true">→</span></a><a href="#hoc-vien" className="ph-feature"><span className="ph-feature-icon ph-feature-icon-yellow" aria-hidden="true">✦</span><div><p>ĐỒNG HÀNH MỖI NGÀY</p><h2>Học trên lớp, luyện ở nhà</h2><span>Kết nối học liệu, bài luyện và tiến độ.</span></div><span className="ph-feature-arrow" aria-hidden="true">→</span></a></section>
      <section id="ve-chung-toi" className="ph-section ph-about"><div><p className="ph-eyebrow">CHÀO MỪNG BẠN ĐẾN VỚI TRUNG TÂM</p><h2>Học để hiểu.<br /><span>Kết nối để trưởng thành.</span></h2></div><div className="ph-about-copy"><p>Ngoại ngữ mở ra những cuộc trò chuyện mới, cơ hội mới và cách nhìn mới. Chúng tôi xây dựng một trải nghiệm học tập gần gũi, nơi mỗi học viên có thể bắt đầu từ chính khả năng của mình.</p><p>Từ chọn lớp, theo dõi lịch học đến luyện tập và xem kết quả, hành trình của bạn được kết nối trong cùng một không gian.</p><a className="ph-text-link" href="#khoa-hoc">Khám phá hành trình học <span aria-hidden="true">→</span></a></div></section>
      <section id="khoa-hoc" className="ph-program-section"><div className="ph-section"><div className="ph-section-heading"><div><p className="ph-eyebrow">CHỌN ĐIỂM BẮT ĐẦU CỦA BẠN</p><h2>Một mục tiêu.<br /><span>Một lộ trình phù hợp.</span></h2></div><p>Khám phá các hướng học ngoại ngữ.<br />Chương trình và lịch học cụ thể được trung tâm xác nhận khi đăng ký.</p></div><div className="ph-program-grid">{programs.map(program => <article className={`ph-program ${program.className}`} key={program.code}><div className="ph-program-top"><span>{program.tag}</span><span className="ph-program-number">{program.code}</span></div><div className="ph-program-art" aria-hidden="true">{program.className === 'foundation' ? 'Aa' : program.className === 'communication' ? 'Hello!' : 'IELTS'}<span>✦</span></div><h3>{program.name}</h3><p>{program.description}</p><a href="#tu-van">Tìm hiểu lộ trình <span aria-hidden="true">↗</span></a></article>)}</div></div></section>
      <section id="giang-vien" className="ph-section ph-teachers"><div><p className="ph-eyebrow">GIẢNG VIÊN & PHƯƠNG PHÁP</p><h2>Người đồng hành.<br /><span>Không chỉ là người dạy.</span></h2><p className="ph-section-description">Một buổi học tốt bắt đầu từ sự tương tác. Giảng viên cùng học viên thực hành, nhận phản hồi và từng bước làm rõ điều cần cải thiện.</p><a className="ph-button ph-button-outline" href="#tu-van">Trao đổi với trung tâm <span aria-hidden="true">→</span></a></div><div className="ph-method-list">{[['01', 'Hiểu điểm bắt đầu', 'Đối chiếu trình độ và mục tiêu để chọn lớp phù hợp.'], ['02', 'Thực hành chủ động', 'Tăng cơ hội sử dụng ngôn ngữ qua bài tập và tình huống.'], ['03', 'Phản hồi rõ ràng', 'Theo dõi kết quả học tập để điều chỉnh kế hoạch luyện tập.']].map(([n, title, text]) => <article key={n}><span>{n}</span><div><h3>{title}</h3><p>{text}</p></div></article>)}</div></section>
      <section id="hoc-vien" className="ph-students"><div className="ph-student-photo"><img src="/images/center-community.jpg" alt="Các bạn trẻ cùng học và trao đổi bên nhau" loading="lazy" /><span>Ảnh minh họa trải nghiệm học tập</span></div><div className="ph-student-copy"><p className="ph-eyebrow">KHÔNG GIAN CỦA HỌC VIÊN</p><h2>Mỗi ngày một chút.<br /><span>Mỗi bước một tiến bộ.</span></h2><p>Lịch học, học liệu, bài luyện và kết quả luôn ở cùng một nơi. Đăng nhập để tiếp tục hành trình của bạn, trên lớp và cả khi ở nhà.</p><ul><li>Lịch học và thông báo từ trung tâm</li><li>Bài luyện cá nhân với AI khi được trung tâm bật</li><li>Theo dõi kết quả và tiến độ học tập</li></ul><Link className="ph-button" to="/login">Vào không gian học tập <span aria-hidden="true">→</span></Link></div></section>
      <section id="tu-van" className="ph-section ph-consultation"><span className="ph-consultation-spark" aria-hidden="true">✦</span><div><p className="ph-eyebrow">SẴN SÀNG CHO BƯỚC TIẾP THEO?</p><h2>Bắt đầu hành trình<br />ngoại ngữ của bạn.</h2><p>Tạo tài khoản để chọn trung tâm, tìm hiểu lớp phù hợp và gửi yêu cầu đăng ký. Trung tâm sẽ xác nhận điều kiện và lịch học.</p></div><div className="ph-consultation-actions"><Link className="ph-button" to="/register">Đăng ký ngay <span aria-hidden="true">↗</span></Link><Link to="/login">Đã có tài khoản? Đăng nhập →</Link></div></section>
    </main><footer className="ph-footer"><div><strong>TRUNG TÂM NGOẠI NGỮ</strong><p>Học vui hơn. Kết nối xa hơn.</p></div><nav aria-label="Liên kết cuối trang"><a href="#ve-chung-toi">Về chúng tôi</a><a href="#khoa-hoc">Khóa học</a><Link to="/login">Đăng nhập</Link><Link to="/register">Đăng ký</Link></nav><p className="ph-footer-note">Không gian học tập được kết nối cùng SynapseLMS.</p></footer>
    <PublicFaqChat />
  </div>
}
