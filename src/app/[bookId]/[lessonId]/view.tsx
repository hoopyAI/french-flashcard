"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { books } from "@/data/books";
import {
  getProgress,
  isMastered,
  saveProgress,
  setMastered,
} from "@/lib/storage";

type Section = "reading" | "listening" | null;
type SectionMode = "reading" | "listening" | "all";
type TransLang = "zh" | "en";
type StudyMode = "study" | "recite";

interface CardState {
  id: string;
  front: string;
  zh: string;
  en: string;
  mastered: boolean;
  section: Section;
}

const SECTION_KEY = (b: string, l: string) => `section_${b}_${l}`;
const STUDY_MODE_KEY = "default_study_mode";
const TRANS_LANG_KEY = "default_trans_lang";

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
  const [sectionMode, setSectionMode] = useState<SectionMode>("all");
  const [filterMode, setFilterMode] = useState<"all" | "unmastered">("all");
  const [studyMode, setStudyMode] = useState<StudyMode>("recite");
  const [transLang, setTransLang] = useState<TransLang>("zh");

  // Restore global preferences on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedMode = window.localStorage.getItem(STUDY_MODE_KEY);
    if (savedMode === "study" || savedMode === "recite") setStudyMode(savedMode);

    const savedLang = window.localStorage.getItem(TRANS_LANG_KEY);
    if (savedLang === "zh" || savedLang === "en") setTransLang(savedLang);
  }, []);

  const updateStudyMode = useCallback((mode: StudyMode) => {
    setStudyMode(mode);
    setRevealed(false);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STUDY_MODE_KEY, mode);
    }
  }, []);

  const updateTransLang = useCallback((lang: TransLang) => {
    setTransLang(lang);
    setRevealed(false);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(TRANS_LANG_KEY, lang);
    }
  }, []);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [toast, setToast] = useState("");

  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const didRestoreRef = useRef(false);

  // Load cards + choose default section on mount
  useEffect(() => {
    if (!lesson) return;
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
        id: card.id,
        front: card.front,
        zh: card.zh,
        en: card.en,
        mastered: isMastered(bookId, lessonId, card.id),
        section,
      });
    }
    setAllCards(annotated);

    const hasReading = annotated.some((c) => c.section === "reading");
    const hasListening = annotated.some((c) => c.section === "listening");

    // Pick default: saved choice > reading > listening > all
    let initialMode: SectionMode = "all";
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem(SECTION_KEY(bookId, lessonId));
      if (
        (saved === "reading" && hasReading) ||
        (saved === "listening" && hasListening) ||
        saved === "all"
      ) {
        initialMode = saved as SectionMode;
      } else if (hasReading && hasListening) {
        initialMode = "reading";
      } else if (hasReading) {
        initialMode = "reading";
      } else if (hasListening) {
        initialMode = "listening";
      }
    }
    setSectionMode(initialMode);
    didRestoreRef.current = false;
  }, [bookId, lessonId, lesson]);

  const readingExists = useMemo(
    () => allCards.some((c) => c.section === "reading"),
    [allCards]
  );
  const listeningExists = useMemo(
    () => allCards.some((c) => c.section === "listening"),
    [allCards]
  );
  const showSectionTabs = readingExists && listeningExists;

  // Derive visible cards
  const cards = useMemo(() => {
    let list = allCards;
    if (sectionMode === "reading") {
      list = list.filter((c) => c.section === "reading");
    } else if (sectionMode === "listening") {
      list = list.filter((c) => c.section === "listening");
    }
    if (filterMode === "unmastered") {
      list = list.filter((c) => !c.mastered);
    }
    return list;
  }, [allCards, sectionMode, filterMode]);

  // Restore lastVisited once after initial cards are computed; reset to 0 on
  // subsequent section/filter changes.
  useEffect(() => {
    if (cards.length === 0) return;
    if (!didRestoreRef.current) {
      didRestoreRef.current = true;
      const progress = getProgress(bookId, lessonId);
      if (progress.lastVisited) {
        const idx = cards.findIndex((c) => c.id === progress.lastVisited);
        if (idx >= 0) {
          setCurrentIndex(idx);
          return;
        }
      }
    }
    setCurrentIndex((prev) => (prev >= cards.length ? cards.length - 1 : prev));
  }, [cards, bookId, lessonId]);

  // Persist current section choice
  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(SECTION_KEY(bookId, lessonId), sectionMode);
  }, [sectionMode, bookId, lessonId]);

  // Persist lastVisited
  useEffect(() => {
    const card = cards[currentIndex];
    if (card) {
      const progress = getProgress(bookId, lessonId);
      progress.lastVisited = card.id;
      saveProgress(bookId, lessonId, progress);
    }
  }, [currentIndex, cards, bookId, lessonId]);

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
      const newAll = allCards.map((c) =>
        c.id === card.id ? { ...c, mastered } : c
      );
      setAllCards(newAll);

      // Recompute what cards will look like after state update
      let next = newAll;
      if (sectionMode === "reading") next = next.filter((c) => c.section === "reading");
      else if (sectionMode === "listening") next = next.filter((c) => c.section === "listening");
      if (filterMode === "unmastered") next = next.filter((c) => !c.mastered);

      if (next.length === 0) {
        showToast("全部已掌握！", true);
        return;
      }

      const stillVisible = next.some((c) => c.id === card.id);
      if (!stillVisible) {
        // Card dropped out of view (unmastered filter): stay at current index
        // (which now shows the next card) unless we're past the end.
        const nextIdx = Math.min(currentIndex, next.length - 1);
        setCurrentIndex(nextIdx);
        setRevealed(false);
        return;
      }

      if (currentIndex >= next.length - 1) {
        showToast("完成！", true);
      } else {
        setCurrentIndex(currentIndex + 1);
        setRevealed(false);
      }
    },
    [cards, currentIndex, allCards, bookId, lessonId, sectionMode, filterMode, showToast]
  );

  const handleSetSection = useCallback(
    (mode: SectionMode) => {
      if (mode === sectionMode) return;
      setSectionMode(mode);
      setCurrentIndex(0);
      setRevealed(false);
      didRestoreRef.current = true; // don't restore across section switches
    },
    [sectionMode]
  );

  const handleToggleFilter = useCallback(() => {
    const newMode = filterMode === "all" ? "unmastered" : "all";
    // Preview: any unmastered in current section?
    if (newMode === "unmastered") {
      const inSection = allCards.filter((c) =>
        sectionMode === "all"
          ? true
          : c.section === sectionMode
      );
      if (inSection.every((c) => c.mastered)) {
        showToast("全部已掌握！");
        return;
      }
    }
    setFilterMode(newMode);
    setCurrentIndex(0);
    setRevealed(false);
  }, [filterMode, allCards, sectionMode, showToast]);

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

  // Choose the displayed translation; fall back to the other language if
  // the selected slot is empty.
  const chosenTrans = currentCard
    ? (transLang === "zh"
        ? currentCard.zh || currentCard.en
        : currentCard.en || currentCard.zh) || ""
    : "";
  const frText = currentCard?.front ?? "";
  // Study mode: show both translation and French together; no flipping.
  // Recite mode: show translation, reveal French on tap.
  const isStudy = studyMode === "study";
  const canReveal = !isStudy && !!frText;
  const showFrench = isStudy || revealed;
  const hintLabel = "点击查看法语";

  function sizeFor(text: string | undefined): string {
    const n = text?.length ?? 0;
    if (n > 260) return "text-xs leading-6";
    if (n > 170) return "text-sm leading-6";
    if (n > 90) return "text-base leading-7";
    return "text-lg leading-8";
  }
  const transSize = sizeFor(chosenTrans);
  const frSize = sizeFor(frText);

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

        <span className="flex-1" />
        {/* Translation language toggle: 中 vs 英 (global, persisted) */}
        <button
          onClick={() => updateTransLang(transLang === "zh" ? "en" : "zh")}
          className="flex items-center gap-1 bg-transparent border-none cursor-pointer font-[inherit]"
          title="切换译文语言（中/英），全站记忆"
        >
          <span
            className={`text-sm px-1 ${transLang === "zh" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            中
          </span>
          <span className="text-gray-300 text-sm">/</span>
          <span
            className={`text-sm px-1 ${transLang === "en" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            En
          </span>
        </button>

        {/* Study mode toggle: 学习 (both visible) vs 背诵 (flip to reveal) */}
        <button
          onClick={() => updateStudyMode(studyMode === "study" ? "recite" : "study")}
          className="flex items-center gap-1 bg-transparent border-none cursor-pointer font-[inherit]"
          title="切换模式（学习：同时显示译文+法语；背诵：点击翻面），全站记忆"
        >
          <span
            className={`text-sm px-1 ${studyMode === "study" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            学习
          </span>
          <span className="text-gray-300 text-sm">/</span>
          <span
            className={`text-sm px-1 ${studyMode === "recite" ? "text-[var(--color-primary)] font-bold" : "text-gray-400"}`}
          >
            背诵
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

      {/* Section tabs */}
      {showSectionTabs && (
        <div className="flex gap-2 mb-3 px-1">
          <button
            onClick={() => handleSetSection("reading")}
            className={`flex-1 py-2 rounded-xl text-sm font-semibold cursor-pointer font-[inherit] border-[2px] transition-colors ${
              sectionMode === "reading"
                ? "bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-[2px_2px_0_var(--color-primary-light)]"
                : "bg-white text-[var(--color-primary)] border-[var(--color-primary)]/40"
            }`}
          >
            📖 阅读 Lecture
          </button>
          <button
            onClick={() => handleSetSection("listening")}
            className={`flex-1 py-2 rounded-xl text-sm font-semibold cursor-pointer font-[inherit] border-[2px] transition-colors ${
              sectionMode === "listening"
                ? "bg-amber-500 text-white border-amber-500 shadow-[2px_2px_0_rgba(245,158,11,0.25)]"
                : "bg-white text-amber-700 border-amber-300"
            }`}
          >
            🎧 听力 Oral
          </button>
        </div>
      )}

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
            className={`card-base w-full overflow-y-auto relative flex flex-col justify-center ${
              canReveal ? "cursor-pointer" : ""
            }`}
            style={{ height: "70%" }}
            onClick={() => canReveal && setRevealed(!revealed)}
          >
            {/* Translation (always visible) */}
            <div className="p-5 text-center">
              <p className={`${transSize} text-[var(--color-fg)]`}>
                {chosenTrans}
              </p>
            </div>

            {/* French */}
            {showFrench && !!frText && (
              <div className="p-5 pt-3 mx-5 border-t border-gray-200 text-center">
                <p className={`${frSize} text-[var(--color-primary)]`}>
                  {frText}
                </p>
              </div>
            )}

            {/* Tap hint (recite mode only) */}
            {canReveal && !revealed && (
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
