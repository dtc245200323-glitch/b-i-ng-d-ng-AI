import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { Language } from './i18n'
import { errorMessage } from './i18n'
import { createRequestKey, requestErrorCode } from './requestKey'
import { Icon } from './ui/Icon'

type Exercise = {id: string; topic: string; level: string; difficulty: string; questions: {stem: string; options: string[]}[]; completed_at: string | null; correct_count?: number; score_percent?: number; answers?: number[]; feedback?: {correct_index: number; explanation: string}[]}
type History = {id: string; topic: string; level: string; question_count: number; score_percent: number | null; completed_at: string | null}

export function PracticeSets({language}: {language: Language}) {
  const vi = language === 'vi'
  const [courses, setCourses] = useState<{id: string; name: string}[]>([]), [course, setCourse] = useState('')
  const [topic, setTopic] = useState(''), [level, setLevel] = useState('A2'), [difficulty, setDifficulty] = useState('medium'), [count, setCount] = useState(10)
  const [exercise, setExercise] = useState<Exercise | null>(null), [history, setHistory] = useState<History[]>([])
  const [answers, setAnswers] = useState<Record<number, number>>({}), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const pending = useRef<{fingerprint: string; key: string} | null>(null)
  const refresh = () => api<{items: History[]}>('/practice/sets/mine').then(r => setHistory(r.items))
  useEffect(() => { let active = true; Promise.all([api<{items: {id: string; name: string}[]}>('/course-catalog?limit=100'), api<{items: History[]}>('/practice/sets/mine')]).then(([c, h]) => { if (active) { setCourses(c.items); setCourse(c.items[0]?.id || ''); setHistory(h.items) } }).catch(e => { if (active) setError(requestErrorCode(e)) }); return () => { active = false } }, [])
  async function generate() {
    setBusy(true); setError('')
    try {
      const body = {course_id: course, topic: topic.trim(), level: level.trim(), difficulty, question_count: count, locale: language}
      const fingerprint = JSON.stringify(body)
      if (pending.current?.fingerprint !== fingerprint) pending.current = {fingerprint, key: createRequestKey()}
      const row = await api<Exercise>('/practice/sets/generate', 'POST', {...body, request_key: pending.current.key})
      setExercise(row); setAnswers({}); pending.current = null; await refresh()
    } catch (e) { setError(requestErrorCode(e)) } finally { setBusy(false) }
  }
  async function open(id: string) {
    setBusy(true); setError('')
    try { const row = await api<Exercise>(`/practice/sets/${id}`); setExercise(row); setAnswers(Object.fromEntries((row.answers || []).map((a, i) => [i, a]))) }
    catch (e) { setError(requestErrorCode(e)) } finally { setBusy(false) }
  }
  async function submit() {
    if (!exercise) return
    setBusy(true); setError('')
    try { setExercise(await api<Exercise>(`/practice/sets/${exercise.id}/submit`, 'POST', {answers: exercise.questions.map((_, i) => answers[i])})); await refresh() }
    catch (e) { setError(requestErrorCode(e)) } finally { setBusy(false) }
  }
  const answered = exercise?.questions.filter((_, i) => answers[i] !== undefined).length || 0
  return <section className="practice-studio"><header className="practice-studio-heading"><span className="studio-icon"><Icon name="spark" width={28} height={28} /></span><div><p className="eyebrow">AI PRACTICE STUDIO</p><h2>{vi ? 'Bài luyện dành riêng cho bạn' : 'Practice made for you'}</h2><p>{vi ? 'Chọn mục tiêu. Tạo bài. Tiến bộ theo cách của bạn.' : 'Choose a goal. Build an exercise. Learn at your own pace.'}</p></div></header>
    {error && <p role="alert" className="error">{errorMessage(language, error)}</p>}
    <form className="practice-builder" onSubmit={e => { e.preventDefault(); void generate() }}><fieldset disabled={busy}><label>{vi ? 'Khóa học / ngôn ngữ' : 'Course / language'}<select value={course} onChange={e => setCourse(e.target.value)} required><option value="" disabled>{vi ? 'Chọn khóa học' : 'Choose a course'}</option>{courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>{vi ? 'Chủ đề luyện tập' : 'Practice topic'}<input value={topic} onChange={e => setTopic(e.target.value)} placeholder={vi ? 'Ví dụ: giao tiếp tại sân bay' : 'e.g. At the airport'} minLength={2} maxLength={200} required /></label><label>{vi ? 'Trình độ mục tiêu' : 'Target level'}<input value={level} onChange={e => setLevel(e.target.value)} required maxLength={100} placeholder="A2 / IELTS 5.5" /></label><label>{vi ? 'Độ khó' : 'Difficulty'}<select value={difficulty} onChange={e => setDifficulty(e.target.value)}><option value="easy">{vi ? 'Khởi động' : 'Easy'}</option><option value="medium">{vi ? 'Vừa sức' : 'Medium'}</option><option value="hard">{vi ? 'Thử thách' : 'Hard'}</option></select></label><label>{vi ? 'Số câu (1–20)' : 'Questions (1–20)'}<input type="number" min={1} max={20} required value={count} onChange={e => setCount(Number(e.target.value))} /></label><button className="primary" disabled={busy || !course}><Icon name="spark" />{busy ? (vi ? 'Đang xử lý…' : 'Working…') : (vi ? 'Tạo bài luyện' : 'Generate exercise')}</button></fieldset><small>{vi ? 'Bài tự luyện không cộng vào điểm chính thức hoặc chuỗi bài đã duyệt. Cần trung tâm bật nguồn AI; nếu chưa sẵn sàng, bạn vẫn có thể làm bài đã duyệt bên dưới.' : 'Personal exercises do not change official grades or approved-practice streaks. Your center must enable AI; approved exercises below remain available.'}</small></form>
    {exercise && <div className="exercise-workspace"><div className="exercise-heading"><div><p className="eyebrow">{exercise.level} · {exercise.questions.length} {vi ? 'CÂU HỎI' : 'QUESTIONS'}</p><h3>{exercise.topic}</h3></div><span className="status">{exercise.completed_at ? `${exercise.score_percent}%` : `${answered}/${exercise.questions.length}`}</span></div><progress max={exercise.questions.length} value={exercise.completed_at ? exercise.questions.length : answered} />
      {exercise.completed_at && <p role="status">{vi ? `Bạn trả lời đúng ${exercise.correct_count}/${exercise.questions.length} câu. Cùng xem lại để tiến bộ nhé.` : `${exercise.correct_count}/${exercise.questions.length} correct. Review your feedback below.`}</p>}
      <div className="exercise-questions">{exercise.questions.map((q, i) => <fieldset className="exercise-question" key={i} disabled={busy || !!exercise.completed_at}><legend><span>{String(i + 1).padStart(2, '0')}</span> {q.stem}</legend>{q.options.map((option, index) => <label className={`exercise-option ${answers[i] === index ? 'selected' : ''}`} key={index}><input type="radio" name={`set-${exercise.id}-${i}`} checked={answers[i] === index} onChange={() => setAnswers(a => ({...a, [i]: index}))} /><span>{String.fromCharCode(65 + index)}</span>{option}</label>)}{exercise.feedback?.[i] && <div className="exercise-feedback"><strong>{answers[i] === exercise.feedback[i].correct_index ? (vi ? 'Chính xác!' : 'Correct!') : (vi ? 'Cùng xem lại nhé' : 'Review this answer')}</strong><p>{vi ? 'Đáp án' : 'Answer'}: {q.options[exercise.feedback[i].correct_index]}</p><p>{exercise.feedback[i].explanation}</p></div>}</fieldset>)}</div>
      {!exercise.completed_at && <button className="primary" disabled={busy || answered !== exercise.questions.length} onClick={() => void submit()}>{vi ? 'Nộp bài & xem giải thích' : 'Submit & review feedback'} <Icon name="arrow" /></button>}</div>}
    {!!history.length && <section className="practice-history"><h3>{vi ? 'Hành trình luyện tập' : 'Practice history'}</h3><div className="practice-history-list">{history.map(row => <button disabled={busy} key={row.id} onClick={() => void open(row.id)}><Icon name="book" /><span><strong>{row.topic}</strong><small>{row.level} · {row.question_count} {vi ? 'câu' : 'questions'}</small></span><span>{row.completed_at ? `${row.score_percent}%` : (vi ? 'Tiếp tục' : 'Continue')} →</span></button>)}</div></section>}
  </section>
}
