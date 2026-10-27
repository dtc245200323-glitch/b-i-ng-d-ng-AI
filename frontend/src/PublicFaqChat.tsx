import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import './public-faq-chat.css'

const faqs = [
  { question: 'Trung tâm có những khóa học nào?', keywords: ['khoa hoc', 'chuong trinh', 'ielts', 'giao tiep', 'nen tang'], answer: 'Bạn có thể tìm hiểu các hướng học tiếng Anh nền tảng, giao tiếp và định hướng IELTS tại mục Khóa học trên trang chủ. Khóa đang mở và lớp phù hợp cần được trung tâm xác nhận theo trình độ, mục tiêu và chỗ trống.' },
  { question: 'Học phí và cách thanh toán thế nào?', keywords: ['hoc phi', 'thanh toan', 'dong tien', 'gia', 'chi phi'], answer: 'Học phí phụ thuộc vào khóa học và cấu hình của trung tâm. Sau khi yêu cầu đăng ký được duyệt, bạn có thể xem hóa đơn, số tiền phải trả và các kỳ thanh toán trong tài khoản. Hệ thống hỗ trợ ghi nhận tiền mặt hoặc chuyển khoản; chuyển khoản cần mã tham chiếu. Hãy xác nhận mức phí và thông tin nhận tiền với trung tâm trước khi thanh toán.' },
  { question: 'Tôi xem lịch học ở đâu?', keywords: ['lich hoc', 'gio hoc', 'buoi hoc', 'thoi gian', 'lich'], answer: 'Sau khi được xếp lớp, đăng nhập và mở mục Học tập của tôi hoặc lịch học để xem các buổi học. Lịch cụ thể tùy lớp; bạn có thể cung cấp khung giờ rảnh khi gửi yêu cầu đăng ký để trung tâm tìm lớp phù hợp. Thay đổi lịch được thông báo trong tài khoản.' },
  { question: 'Làm sao đăng ký học tại trung tâm?', keywords: ['dang ky', 'tao tai khoan', 'ghi danh', 'tuyen sinh'], answer: 'Chọn Đăng ký, tạo tài khoản học viên và chọn trung tâm đang mở đăng ký hoặc sử dụng mã mời hợp lệ. Sau đó đăng nhập, vào Tuyển sinh, chọn khóa học và gửi yêu cầu kèm lịch rảnh. Trung tâm sẽ xét duyệt, xác nhận học phí và xếp lớp phù hợp.' },
  { question: 'Tôi có thể học thử hoặc kiểm tra trình độ không?', keywords: ['hoc thu', 'trinh do', 'dau vao', 'kiem tra', 'xep lop'], answer: 'Để chọn đúng lớp, trung tâm cần xác minh trình độ của bạn. Hãy trao đổi với tư vấn viên về cách kiểm tra đầu vào và lịch kiểm tra. Việc có buổi học thử, mức phí hoặc điều kiện tham gia do trung tâm xác nhận; chatbot chưa có thông tin để cam kết học thử miễn phí.' },
]

const normalize = (value: string) => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim()
type Message = { role: 'bot' | 'user'; text: string }

export function PublicFaqChat() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<Message[]>([{role: 'bot', text: 'Chào bạn! Mình là trợ lý tư vấn tự động. Bạn chọn một câu hỏi bên dưới hoặc nhập câu hỏi về khóa học, học phí, lịch học, đăng ký và kiểm tra trình độ nhé.'}])
  const launcher = useRef<HTMLButtonElement>(null), input = useRef<HTMLInputElement>(null), log = useRef<HTMLDivElement>(null)
  const close = () => { setOpen(false); launcher.current?.focus() }
  useEffect(() => { if (open) input.current?.focus() }, [open])
  useEffect(() => { if (open && log.current) log.current.scrollTop = log.current.scrollHeight }, [open, messages])
  const answer = (question: string, preset?: typeof faqs[number]) => {
    const text = question.trim().slice(0, 300)
    if (!text) return
    const words = ` ${normalize(text)} `
    const match = preset || faqs.map(faq => ({faq, score: faq.keywords.reduce((score, key) => score + (words.includes(` ${key} `) ? key.length : 0), 0)})).filter(item => item.score > 0).sort((a, b) => b.score - a.score)[0]?.faq
    setMessages(history => [...history.slice(-38), {role: 'user', text}, {role: 'bot', text: match?.answer || 'Mình chưa có câu trả lời cho nội dung này. Bạn có thể chọn một trong 5 câu hỏi thường gặp bên dưới. Với thông tin riêng về lớp hoặc hồ sơ của bạn, hãy đăng nhập để xem hoặc trao đổi trực tiếp với trung tâm.'}])
    setDraft('')
  }
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); answer(draft) }
  return <div className="ph-chat-widget">
    {open && <section id="public-faq-chat" className="ph-chat-panel" role="dialog" aria-modal="false" aria-labelledby="ph-chat-title" onKeyDown={event => { if (event.key === 'Escape') { event.stopPropagation(); close() } }}>
      <header className="ph-chat-header"><span className="ph-chat-avatar" aria-hidden="true">✦</span><div><h2 id="ph-chat-title">Tư vấn tự động</h2><p>Giải đáp nhanh · Trung tâm ngoại ngữ</p></div><button type="button" onClick={close} aria-label="Đóng chatbot tư vấn">×</button></header>
      <div ref={log} className="ph-chat-log" role="log" aria-label="Cuộc trò chuyện tư vấn" aria-live="polite" aria-relevant="additions">{messages.map((message, index) => <div className={`ph-chat-message ${message.role}`} key={index}><span className="ph-chat-speaker">{message.role === 'bot' ? 'Trợ lý' : 'Bạn'}</span><p>{message.text}</p></div>)}</div>
      <div className="ph-chat-questions"><p>5 câu hỏi thường gặp</p><div>{faqs.map(faq => <button key={faq.question} type="button" onClick={() => answer(faq.question, faq)}>{faq.question}</button>)}</div></div>
      <form className="ph-chat-form" onSubmit={submit}><label className="ph-chat-sr-only" htmlFor="ph-chat-input">Nhập câu hỏi tư vấn</label><input ref={input} id="ph-chat-input" value={draft} onChange={event => setDraft(event.target.value)} maxLength={300} placeholder="Nhập câu hỏi của bạn…" autoComplete="off" /><button type="submit" aria-label="Gửi câu hỏi" disabled={!draft.trim()}>↑</button></form>
      <div className="ph-chat-footer"><span>Trả lời theo câu hỏi thường gặp</span><Link to="/register">Đăng ký học →</Link></div>
    </section>}
    <button ref={launcher} type="button" className="ph-chat-launcher" onClick={() => open ? close() : setOpen(true)} aria-expanded={open} aria-controls="public-faq-chat" aria-label={open ? 'Thu gọn chatbot tư vấn' : 'Mở chatbot tư vấn'}><svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M20 11.5a8 8 0 0 1-8 8H5l-3 2v-7a8 8 0 1 1 18-3.5Z" /><path d="M7 10h10M7 14h6" /></svg><span>Tư vấn nhanh</span></button>
  </div>
}
