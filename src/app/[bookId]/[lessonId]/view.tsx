"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { books } from "@/data/books";
import {
  getProgress,
  isMastered,
  saveProgress,
  setMastered,
} from "@/lib/storage";

type Section = "reading" | "listening" | null;

interface CardState {
  id: string;
  front: string;
  back: string;
  mastered: boolean;
  section: Section;
}

export default function CardsView({
  bookId,
  lessonId,
}: {
  bookId: string;
  lessonId: string;
}) {
  const router = useRouter();

  const book = books.find((b) => b.id === bookId);
  const lesson = book?.lessons.find((l) => l.id === lessonId);

  const [allCards, setAllCards] = useState<CardState[]>([]);
  const [cards, setCards] = useState<CardState[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [filterMode, setFilterMode] = useState<"all" | "unmastered">("all");
  // "cn" = show Chinese first, "fr" = show French first
  const [showMode, setShowMode] = useState<"cn" | "fr">("cn");
  const [toast, setToast] = useState("");

  const touchStartX = useRef(0);
  const touchStartY = useRef(0);

  useEffect(() => {
    if (!lesson) return;
    // Walk original card order once, tracking which section each card belongs to
    // (via the s_read / s_listen marker cards), then drop the markers so they
    // don't appear in the flashcard flow.
    let section: Section = null;
    const annotated: CardState[] = [];
    for (const card of lesson.cards) {
      if (card.id === "s_read") {
        section = "reading";
        continue;
      }
      if (card.id === "s_listen") {
        section = "listening";
        continue;
      }
      if (card.id.startsWith("s_")) continue;
      annotated.push({
        ...card,
        mastered: isMastered(bookId, lessonId, card.id),
        section,
      });
    }
    setAllCards(annotated);
    setCards(annotated);

    const progress = getProgress(bookId, lessonId);
    if (progress.lastVisited) {
      const idx = annotated.findIndex((c) => c.id === progress.lastVisited);
      if (idx > 0) setCurrentIndex(idx);
    }
  }, [bookId, lessonId, lesson]);

  const showToast = useCallback(
    (msg: string, thenGoBack = false) => {
      setToast(msg);
      setTimeout(() => {
        setToast("");
        if (thenGoBack) router.back();
      }, 1500);
    },
    [router]
  );

  const goTo = useCallback(
    (idx: number) => {
      if (idx >= 0 && idx < cards.length) {
        setCurrentIndex(idx);
        setRevealed(false);
      }
    },
    [cards.length]
  );

  const handleSetMastered = useCallback(
    (mastered: boolean) => {
      const card = cards[currentIndex];
      if (!card) return;

      setMastered(bookId, lessonId, card.id, mastered);

      const updatedAll = allCards.map((c) =>
        c.id === card.id ? { ...c, mastered } : c
      );
      setAllCards(updatedAll);

      const updatedCards = cards.map((c) =>
        c.id === card.id ? { ...c, mastered } : c
      );

      if (filterMode === "unmastered" && mastered) {
        const filtered = updatedCards.filter((c) => c.id !== card.id);
        if (filtered.length === 0) {
          showToast("全部已掌握！", true);
          return;
        }
        const newIndex = Math.min(currentIndex, filtered.length - 1);
        setCards(filtered);
        setCurrentIndex(newIndex);
        setRevealed(false);
        return;
      }

      setCards(updatedCards);

      if (currentIndex >= updatedCards.length - 1) {
        showToast("完成！", true);
      } else {
        setCurrentIndex(currentIndex + 1);
        setRevealed(false);
      }
    },
    [cards, currentIndex, allCards, bookId, lessonId, filterMode, showToast]
  );

  const handleToggleFilter = useCallback(() => {
    const newMode = filterMode === "all" ? "unmastered" : "all";
    if (newMode === "unmastered") {
      const filtered = allCards.filter((c) => !c.mastered);
      if (filtered.length === 0) {
        showToast("全部已掌握！");
        return;
      }
      setCards(filtered);
    } else {
      setCards([...allCards]);
    }
    setFilterMode(newMode);
    setCurrentIndex(0);
    setRevealed(false);
  }, [filterMode, allCards, showToast]);

  useEffect(() => {
    const card = cards[currentIndex];
    if (card) {
      const progress = getProgress(bookId, lessonId);
      progress.lastVisited = card.id;
      saveProgress(bookId, lessonId, progress);
    }
  }, [currentIndex, cards, bookId, lessonId]);

  const onTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
  };

  const onTouchEnd = (e: React.TouchEvent) => {
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = e.changedTouches[0].clientY - touchStartY.current;
    if (Math.abs(dx) < 50 || Math.abs(dy) > Math.abs(dx)) return;
    if (dx < 0) goTo(currentIndex + 1);
    else goTo(currentIndex - 1);
  };

  if (!lesson) return <div className="p-5">课文未找到</div>;

  const progressText =
    cards.length > 0 ? `${currentIndex + 1}/${cards.length}` : "0/0";
  const currentCard = cards[currentIndex];

  // front = French, back = Chinese/English in data
  // showMode determines which is visible first
  const visibleText =
    showMode === "cn" ? currentCard?.back : currentCard?.front;
  const hiddenText =
    showMode === "cn" ? currentCard?.front : currentCard?.back;
  const hasHidden = !!hiddenText && hiddenText.length > 0;
  const hintLabel = showMode === "cn" ? "点击查看法语" : "点击查看中文";

  // Scale font down for long sentences so they fit comfortably in the card.
  function sizeFor(text: string | undefined): string {
    const n = text?.length ?? 0;
    if (n > 260) return "text-xs leading-6";
    if (n > 170) return "text-sm leading-6";
    if (n > 90) return "text-base leading-7";
    return "text-lg leading-8";
  }
  const visibleSize = sizeFor(visibleText);
  const hiddenSize = sizeFor(hiddenText);

  const sectionLabel =
    currentCard?.section === "reading"
      ? "阅读 · Lecture"
      : currentCard?.section === "listening"
      ? "听力 · Oral"
      : null;

  return (
    <div className="flex flex-col h-dvh p-3 max-w-lg mx-auto">
      {/* Toast */}
      {toast && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
          <div className="bg-[var(--color-primary)] text-white px-6 py-3 rounded-xl text-lg shadow-lg">
            {toast}
          </div>
        </div>
      )}

      {/* Top bar */}
      <div className="flex items-center py-2 px-1 mb-2 gap-3">
        <button
          onClick={() => router.back()}
          className="shrink-0 bg-transparent border-none cursor-pointer text-[var(--color-primary)] text-lg p-0 leading-none"
        >
          ←
        </button>
        <span className="text-base font-bold text-[var(--color-primary)]">
          {progressText}
        </span>

        {sectionLabel && (
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full tracking-wide ${
              currentCard?.section === "reading"
                ? "bg-[var(--color-primary-light)] text-[var(--color-primary)]"
                : "bg-amber-100 text-amber-700"
            }`}
          >
            {sectionLabel}
          </span>
        )}

        <span className="flex-1" />
        {/* Language mode toggle */}
        <button
          onClick={() => {
            setShowMode(showMode === "cn" ? "fr" : "cn");
            setRevealed(false);
          }}
          className="flex items-center gap-1 bg-transparent border-none cursor-pointer font-[inherit]"
        >
          <span
            className={`text-sm px-1 ${showMode === "cn" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            中
          </span>
          <span className="text-gray-300 text-sm">/</span>
          <span
            className={`text-sm px-1 ${showMode === "fr" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            Fr
          </span>
        </button>

        {/* Filter toggle */}
        <button
          onClick={handleToggleFilter}
          className="flex items-center gap-1 bg-transparent border-none cursor-pointer font-[inherit]"
        >
          <span
            className={`text-sm px-1 ${filterMode === "all" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            全部
          </span>
          <span className="text-gray-300 text-sm">|</span>
          <span
            className={`text-sm px-1 ${filterMode === "unmastered" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            未掌握
          </span>
        </button>
      </div>

      {/* Card area */}
      <div
        className="flex-1 flex items-center justify-center gap-2 px-1"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {/* Left arrow */}
        <button
          onClick={() => goTo(currentIndex - 1)}
          disabled={currentIndex === 0}
          className="shrink-0 w-10 h-10 flex items-center justify-center rounded-full border-2 border-[var(--color-primary)] bg-white text-[var(--color-primary)] text-lg cursor-pointer disabled:opacity-20 disabled:cursor-default"
        >
          ‹
        </button>

        {/* Card */}
        {currentCard && (
          <div
            className="card-base w-full overflow-y-auto cursor-pointer relative flex flex-col justify-center"
            style={{ height: "70%" }}
            onClick={() => hasHidden && setRevealed(!revealed)}
          >
            {/* Primary text */}
            <div className="p-5 text-center">
              <p
                className={`${visibleSize} ${
                  showMode === "cn"
                    ? "text-[var(--color-fg)]"
                    : "text-[var(--color-primary)]"
                }`}
              >
                {visibleText}
              </p>
            </div>

            {/* Revealed text */}
            {hasHidden && revealed && (
              <div className="p-5 pt-3 mx-5 border-t border-gray-200 text-center">
                <p
                  className={`${hiddenSize} ${
                    showMode === "cn"
                      ? "text-[var(--color-primary)]"
                      : "text-gray-600"
                  }`}
                >
                  {hiddenText}
                </p>
              </div>
            )}

            {/* Tap hint */}
            {hasHidden && !revealed && (
              <div className="absolute bottom-3 left-0 right-0 text-center text-xs text-gray-300">
                {hintLabel}
              </div>
            )}
          </div>
        )}

        {/* Right arrow */}
        <button
          onClick={() => goTo(currentIndex + 1)}
          disabled={currentIndex >= cards.length - 1}
          className="shrink-0 w-10 h-10 flex items-center justify-center rounded-full border-2 border-[var(--color-primary)] bg-white text-[var(--color-primary)] text-lg cursor-pointer disabled:opacity-20 disabled:cursor-default"
        >
          ›
        </button>
      </div>

      {/* Bottom bar */}
      {cards.length > 0 && (
        <div className="flex justify-between items-center py-3 px-1 gap-2">
          <button
            onClick={() => handleSetMastered(false)}
            className="flex-1 py-2.5 rounded-xl text-base cursor-pointer font-[inherit] bg-white text-[var(--color-primary)] border-[2.5px] border-[var(--color-primary)] shadow-[3px_3px_0_var(--color-primary-light)] active:translate-y-[1px] active:shadow-[2px_2px_0_var(--color-primary-light)]"
          >
            ✗ 未掌握
          </button>
          <span
            className={`text-xs ${currentCard?.mastered ? "text-[var(--color-primary)]" : "text-gray-400"}`}
          >
            {currentCard?.mastered ? "已掌握" : "未掌握"}
          </span>
          <button
            onClick={() => handleSetMastered(true)}
            className="flex-1 py-2.5 rounded-xl text-base cursor-pointer font-[inherit] bg-[var(--color-primary)] text-white border-[2.5px] border-[var(--color-primary)] shadow-[3px_3px_0_var(--color-primary-light)] active:translate-y-[1px] active:shadow-[2px_2px_0_var(--color-primary-light)]"
          >
            ✓ 已掌握
          </button>
        </div>
      )}
    </div>
  );
}
