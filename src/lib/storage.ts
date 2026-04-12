const STORAGE_KEY_PREFIX = "progress_";

interface Progress {
  mastered: string[];
  lastVisited: string;
}

function getKey(bookId: string, lessonId: string): string {
  return STORAGE_KEY_PREFIX + bookId + "-" + lessonId;
}

export function getProgress(bookId: string, lessonId: string): Progress {
  if (typeof window === "undefined") return { mastered: [], lastVisited: "" };
  const raw = localStorage.getItem(getKey(bookId, lessonId));
  if (!raw) return { mastered: [], lastVisited: "" };
  return JSON.parse(raw);
}

export function saveProgress(
  bookId: string,
  lessonId: string,
  progress: Progress
) {
  localStorage.setItem(getKey(bookId, lessonId), JSON.stringify(progress));
}

export function setMastered(
  bookId: string,
  lessonId: string,
  cardId: string,
  mastered: boolean
): boolean {
  const progress = getProgress(bookId, lessonId);
  if (mastered) {
    if (!progress.mastered.includes(cardId)) {
      progress.mastered.push(cardId);
    }
  } else {
    progress.mastered = progress.mastered.filter((id) => id !== cardId);
  }
  saveProgress(bookId, lessonId, progress);
  return mastered;
}

export function isMastered(
  bookId: string,
  lessonId: string,
  cardId: string
): boolean {
  const progress = getProgress(bookId, lessonId);
  return progress.mastered.includes(cardId);
}

export function getMasteredCount(bookId: string, lessonId: string): number {
  const progress = getProgress(bookId, lessonId);
  return progress.mastered.length;
}
