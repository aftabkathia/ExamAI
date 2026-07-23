export type User = {
  id: number;
  email: string;
  full_name: string;
  avatar_url?: string | null;
  current_streak: number;
  longest_streak: number;
};

export type Topic = {
  id: number;
  name: string;
  description: string;
};

export type ExamTrack = {
  id: number;
  code: string;
  name: string;
  category: "academic" | "government" | string;
  description: string;
  icon: string;
  topics: Topic[];
};

export type Question = {
  id: number;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  difficulty: string;
  topic_id: number;
  topic_name?: string | null;
  source?: string | null;
};

export type QuizSession = {
  id: number;
  exam_track_id: number;
  total_questions: number;
  correct_count: number;
  completed: boolean;
  started_at: string;
};

export type AnswerFeedback = {
  is_correct: boolean;
  correct_option: string;
  explanation: string;
  selected_option: string;
  mastery_score: number;
  next_question: Question | null;
  session_completed: boolean;
  session_score: number | null;
  session_total: number | null;
};

export type TopicProgress = {
  topic_id: number;
  topic_name: string;
  exam_name: string;
  attempts_count: number;
  correct_count: number;
  accuracy: number;
  mastery_score: number;
};

export type ProgressDashboard = {
  total_attempts: number;
  total_correct: number;
  overall_accuracy: number;
  current_streak: number;
  longest_streak: number;
  quizzes_completed: number;
  topic_progress: TopicProgress[];
  recent_activity: { date: string; attempts: number; correct: number }[];
  weak_topics: TopicProgress[];
  strong_topics: TopicProgress[];
};

export type TopicNote = {
  id: number;
  topic_id: number;
  topic_name?: string | null;
  exam_name?: string | null;
  title: string;
  summary: string;
  content: string;
  key_points: string[];
  order_index: number;
};

export type EssayPrompt = {
  id: number;
  topic_id: number;
  topic_name?: string | null;
  exam_name?: string | null;
  title: string;
  prompt: string;
  outline: string;
  word_limit: number;
  difficulty: string;
};

export type PastPaperListItem = {
  id: number;
  exam_track_id: number;
  exam_name?: string | null;
  topic_id?: number | null;
  topic_name?: string | null;
  title: string;
  year: string;
  description: string;
  question_count: number;
};

export type PastPaperQuestion = {
  id: number;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_option: string;
  explanation: string;
  order_index: number;
};

export type PastPaper = PastPaperListItem & {
  questions: PastPaperQuestion[];
};
