import { useEffect, useState } from 'react'
import { api, apiContent } from './api'
import type { Language } from './i18n'
import { errorMessage } from './i18n'
import { requestErrorCode } from './requestKey'
import { Icon } from './ui/Icon'

type Report = { students: number; teachers: number; classes: number; collected: number; refunded: number | null; net_cash: number | null; attendance_percent: number | null; completion_percent: number | null; pass_percent: number | null; active_enrollments: number; items: { id: string; code: string; name: string; capacity: number; active_students: number; total_enrollments: number; completed_results: number }[] }
const day = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`

export function Reporting({ language }: { language: Language }) {
  const vi = language === 'vi'
  const today = new Date()
  const [start, setStart] = useState(day(new Date(today.getFullYear(), today.getMonth(), 1)))
  const [end, setEnd] = useState(day(today)), [classId, setClassId] = useState('')
  const [classes, setClasses] = useState<{id: string; name: string}[]>([])
  const [report, setReport] = useState<Report | null>(null), [error, setError] = useState(''), [busy, setBusy] = useState(false)
  const [query, setQuery] = useState(`starts_on=${start}&ends_on=${end}`)
  const [revision, setRevision] = useState(0)
  useEffect(() => { api<{items: {id: string; name: string}[]}>('/classes?status=all&limit=100').then(r => setClasses(r.items)).catch(() => {}) }, [])
  useEffect(() => {
    let active = true
    api<Report>(`/reports/training?${query}`).then(r => { if (active) { setReport(r); setError('') } }).catch(e => { if (active) setError(requestErrorCode(e)) })
    return () => { active = false }
  }, [query, revision])
  const number = (n: number) => new Intl.NumberFormat(vi ? 'vi-VN' : 'en-GB').format(n)
  const money = (n: number | null) => n === null ? '—' : `${number(n)} ₫`
  async function download() {
    setBusy(true)
    try {
      const {blob} = await apiContent(`/reports/training.csv?${query}`)
      if (!blob) throw new Error('REQUEST_FAILED')
      const url = URL.createObjectURL(blob), link = document.createElement('a')
      link.href = url; link.download = 'Synapse-bao-cao-dao-tao.csv'; link.click(); URL.revokeObjectURL(url)
    } catch (e) { setError(requestErrorCode(e)) } finally { setBusy(false) }
  }
  return <section className="reporting-page"><header className="page-heading"><div><p className="eyebrow">{vi ? 'ĐIỀU HÀNH TRUNG TÂM' : 'CENTER OPERATIONS'}</p><h1>{vi ? 'Báo cáo đào tạo' : 'Training reports'}</h1><p>{vi ? 'Một góc nhìn rõ ràng về đào tạo và dòng tiền của trung tâm.' : 'A clear view of learning and center cash flow.'}</p></div><button className="primary" disabled={!report || busy} onClick={() => void download()}>{vi ? 'Xuất báo cáo CSV' : 'Export CSV'} <Icon name="arrow" /></button></header>
    <form className="report-filters card" onSubmit={e => { e.preventDefault(); setReport(null); setError(''); setQuery(`starts_on=${start}&ends_on=${end}${classId ? `&class_id=${classId}` : ''}`); setRevision(n => n + 1) }}>
      <label>{vi ? 'Từ ngày' : 'From'}<input type="date" value={start} required max={end} onChange={e => setStart(e.target.value)} /></label><label>{vi ? 'Đến ngày' : 'To'}<input type="date" value={end} required min={start} onChange={e => setEnd(e.target.value)} /></label><label>{vi ? 'Phạm vi lớp học' : 'Class scope'}<select value={classId} onChange={e => setClassId(e.target.value)}><option value="">{vi ? 'Toàn trung tâm' : 'All classes'}</option>{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><button type="submit">{vi ? 'Xem báo cáo' : 'View report'}</button>
    </form>
    {error && <p role="alert" className="error">{errorMessage(language, error)}</p>}
    {!report && !error && <p role="status">{vi ? 'Đang tổng hợp dữ liệu…' : 'Preparing report…'}</p>}
    {report && <><div className="report-metrics">{[[vi ? 'Học viên' : 'Students', number(report.students)], [vi ? 'Giáo viên' : 'Teachers', number(report.teachers)], [vi ? 'Lớp học' : 'Classes', number(report.classes)], [vi ? 'Đăng ký đang học' : 'Active enrollments', number(report.active_enrollments)]].map(([label, value]) => <article className="card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</div>
      <div className="report-finance"><article className="card"><p className="eyebrow">{vi ? 'DÒNG TIỀN TRONG KỲ' : 'CASH FLOW'}</p><h2>{vi ? 'Thu và hoàn học phí' : 'Tuition and refunds'}</h2><dl><div><dt>{vi ? 'Tiền thu hợp lệ' : 'Valid receipts'}</dt><dd>{money(report.collected)}</dd></div><div><dt>{vi ? 'Tiền hoàn đã chi' : 'Paid refunds'}</dt><dd>{money(report.refunded)}</dd></div><div><dt>{vi ? 'Dòng tiền sau hoàn' : 'Net cash'}</dt><dd>{money(report.net_cash)}</dd></div></dl><small>{vi ? 'Khoản thu đã đảo không được cộng. Dòng tiền khác doanh thu kế toán. Tiền hoàn chỉ tổng hợp ở phạm vi toàn trung tâm.' : 'Reversed payments are excluded. Cash flow differs from accounting revenue. Refunds are available at center scope.'}</small></article>
      <article className="card"><p className="eyebrow">{vi ? 'CHẤT LƯỢNG HỌC TẬP' : 'LEARNING QUALITY'}</p><h2>{vi ? 'Chuyên cần và kết quả' : 'Attendance and results'}</h2>{[[vi ? 'Chuyên cần đã ghi nhận' : 'Recorded attendance', report.attendance_percent], [vi ? 'Kết quả hoàn tất trong kỳ' : 'Results completed this period', report.completion_percent], [vi ? '??t theo ng??ng ?? c?u h?nh' : 'Passed with configured threshold', report.pass_percent ?? null]].map(([label, value]) => <div className="report-progress" key={String(label)}><span>{label}</span><strong>{value === null ? '—' : `${value}%`}</strong><progress max={100} value={typeof value === 'number' ? value : 0} /></div>)}<small>{vi ? 'Chuyên cần: có mặt và đi muộn / buổi đã ghi nhận, trừ nghỉ có phép. Hoàn tất: điểm được công bố, khóa trong kỳ và đủ 100% trọng số / mọi đăng ký. Đây không phải tỷ lệ đỗ. Dữ liệu thiếu hiển thị —.' : 'Attendance excludes excused absences. Completion counts published, locked results with full assessment coverage, divided by all enrollments; it is not a pass rate. Missing data appears as —.'}</small></article></div>
      <article className="card"><h2>{vi ? 'Tình hình từng lớp' : 'Class overview'}</h2><div className="table-scroll"><table><thead><tr>{(vi ? ['Lớp học', 'Đang học / sức chứa', 'Tổng đăng ký', 'Kết quả hoàn tất'] : ['Class', 'Active / capacity', 'All enrollments', 'Completed results']).map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{report.items.map(r => <tr key={r.id}><td><strong>{r.name}</strong><small>{r.code}</small></td><td>{r.active_students} / {r.capacity}</td><td>{r.total_enrollments}</td><td>{r.completed_results}</td></tr>)}</tbody></table></div>{!report.items.length && <p>{vi ? 'Chưa có lớp trong phạm vi đã chọn.' : 'No classes in this scope.'}</p>}</article></>}
  </section>
}

export function AuditTimeline({ language, root }: { language: Language; root: boolean }) {
  const vi = language === 'vi'
  type Log = {id: string; action: string; actor_name: string; target_id: string | null; created_at: string}
  const [page, setPage] = useState<{items: Log[]; total: number} | null>(null)
  const [logRevision, setLogRevision] = useState(0)
  const [action, setAction] = useState(''), [filter, setFilter] = useState(''), [offset, setOffset] = useState(0), [error, setError] = useState('')
  useEffect(() => { let active = true; api<{items: Log[]; total: number}>(`${root ? '/admin' : ''}/audit-logs?offset=${offset}&limit=25&action=${encodeURIComponent(filter)}`).then(r => { if (active) { setPage(r); setError('') } }).catch(e => { if (active) setError(requestErrorCode(e)) }); return () => { active = false } }, [root, offset, filter, logRevision])
  return <section><header className="page-heading"><div><p className="eyebrow">{vi ? 'QUẢN TRỊ & MINH BẠCH' : 'GOVERNANCE'}</p><h1>{vi ? 'Nhật ký hoạt động' : 'Activity log'}</h1><p>{vi ? 'Theo dõi người thực hiện, thời điểm và đối tượng của các thay đổi được ghi nhận.' : 'Review the actor, time and target of recorded changes.'}</p></div></header><form className="report-filters card" onSubmit={e => { e.preventDefault(); setOffset(0); setFilter(action.trim()); setPage(null); setLogRevision(n => n + 1) }}><label>{vi ? 'Mã thao tác' : 'Action code'}<input value={action} onChange={e => setAction(e.target.value)} placeholder="payment.collect" maxLength={80} /></label><button>{vi ? 'Lọc nhật ký' : 'Filter logs'}</button></form>{error && <p className="error" role="alert">{errorMessage(language, error)}</p>}{!page && !error && <p role="status">{vi ? 'Đang tải nhật ký…' : 'Loading logs…'}</p>}{page && <article className="card"><div className="table-scroll"><table><thead><tr>{(vi ? ['Thời điểm', 'Người thực hiện', 'Thao tác', 'Đối tượng'] : ['Time', 'Actor', 'Action', 'Target']).map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{page.items.map(row => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString(vi ? 'vi-VN' : 'en-GB')}</td><td>{row.actor_name || '—'}</td><td><code>{row.action}</code></td><td><code>{row.target_id || '—'}</code></td></tr>)}</tbody></table></div>{!page.items.length && <p>{vi ? 'Chưa có hoạt động phù hợp.' : 'No matching activity.'}</p>}<div className="session-actions"><button disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 25))}>{vi ? 'Trang trước' : 'Previous'}</button><span>{page.total ? offset + 1 : 0}–{Math.min(offset + 25, page.total)} / {page.total}</span><button disabled={offset + 25 >= page.total} onClick={() => setOffset(offset + 25)}>{vi ? 'Trang sau' : 'Next'}</button></div></article>}</section>
}
