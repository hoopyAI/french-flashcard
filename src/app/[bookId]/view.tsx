"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { books } from "@/data/books";
import { getMasteredCount } from "@/lib/storage";

interface LessonInfo {
  id: string;
  title: string;
  totalCards: number;
  masteredCount: number;
}

export default function LessonsView({ bookId }: { bookId: string }) {
  const book = books.find((b) => b.id === bookId);
  const [lessons, setLessons] = useState<LessonInfo[]>([]);

  useEffect(() => {
    if (!book) return;
    setLessons(
      book.lessons.map((lesson) => ({
        id: lesson.id,
        title: lesson.title,
        totalCards: lesson.cards.length,
        masteredCount: getMasteredCount(bookId, lesson.id),
      }))
    );
  }, [book, bookId]);

  useEffect(() => {
    function onVisibility() {
      if (document.visibilityState === "visible" && book) {
        setLessons(
          book.lessons.map((lesson) => ({
            id: lesson.id,
            title: lesson.title,
            totalCards: lesson.cards.length,
            masteredCount: getMasteredCount(bookId, lesson.id),
          }))
        );
      }
    }
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [book, bookId]);

  if (!book) return <div className="p-5">课本未找到</div>;

  return (
    <div className="p-5 max-w-lg mx-auto">
      <Link
        href="/"
        className="text-sm text-[var(--color-primary)] no-underline mb-3 inline-block"
      >
        ← 返回
      </Link>
      <h1 className="text-2xl font-bold mb-5">{book.title}</h1>
      <div className="flex flex-col gap-3">
        {lessons.map((lesson) => {
          const pct =
            lesson.totalCards > 0
              ? (lesson.masteredCount / lesson.totalCards) * 100
              : 0;
          return (
            <Link
              key={lesson.id}
              href={`/${bookId}/${lesson.id}`}
              className="card-base p-4 no-underline text-inherit hover:translate-y-[-2px] transition-transform cursor-pointer block"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-base">{lesson.title}</span>
                <span className="text-xs text-[var(--color-primary)]">
                  {lesson.masteredCount}/{lesson.totalCards}
                </span>
              </div>
              <div className="h-1 bg-gray-200 rounded overflow-hidden">
                <div
                  className="h-full bg-[var(--color-primary)] rounded transition-[width] duration-300"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
