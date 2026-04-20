"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Book, Lesson } from "@/data/books";

type EditState = {
  bookId: string;
  lessonId: string;
  title: string;
  front: string;
  back: string;
};

function lessonToText(lesson: Lesson): { front: string; back: string } {
  return {
    front: lesson.cards.map((c) => c.front).join("\n"),
    back: lesson.cards.map((c) => c.back).join("\n"),
  };
}

export default function EditorPage() {
  const [data, setData] = useState<Book[] | null>(null);
  const [openBook, setOpenBook] = useState<string | null>(null);
  const [edit, setEdit] = useState<EditState | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    const res = await fetch("/api/editor", { cache: "no-store" });
    const json = (await res.json()) as Book[];
    setData(json);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const editingLesson = useMemo(() => {
    if (!edit || !data) return null;
    const book = data.find((b) => b.id === edit.bookId);
    return book?.lessons.find((l) => l.id === edit.lessonId) ?? null;
  }, [edit, data]);

  async function save() {
    if (!edit) return;
    setBusy(true);
    setMsg("");
    try {
      const res = await fetch("/api/editor", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(edit),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "save failed");
      setMsg(`已保存：${json.cards} 张卡片`);
      await refresh();
      setEdit(null);
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function del(bookId: string, lessonId: string, title: string) {
    if (!confirm(`删除《${title}》？无法撤销。`)) return;
    setBusy(true);
    setMsg("");
    try {
      const res = await fetch(
        `/api/editor?bookId=${encodeURIComponent(bookId)}&lessonId=${encodeURIComponent(
          lessonId
        )}`,
        { method: "DELETE" }
      );
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "delete failed");
      setMsg(`已删除`);
      await refresh();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  function startEdit(bookId: string, lesson: Lesson) {
    const { front, back } = lessonToText(lesson);
    setEdit({
      bookId,
      lessonId: lesson.id,
      title: lesson.title,
      front,
      back,
    });
  }

  if (!data) return <div className="p-6 text-gray-500">加载中…</div>;

  const frontLineCount = edit ? edit.front.split(/\r?\n/).filter((l) => l.trim()).length : 0;
  const backLineCount = edit ? edit.back.split(/\r?\n/).filter((l) => l.trim()).length : 0;
  const mismatch = edit && frontLineCount !== backLineCount;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="sticky top-0 z-10 bg-white border-b px-6 py-3 flex items-center gap-4">
        <h1 className="text-lg font-semibold">课文编辑器</h1>
        <span className="text-xs text-gray-400">临时工具 · 保存会直接改写 src/data/books.ts</span>
        <div className="ml-auto text-sm">
          <a href="/" className="text-blue-600 hover:underline">
            返回闪卡
          </a>
        </div>
      </header>

      <div className="flex">
        <aside className="w-[380px] min-h-[calc(100vh-49px)] bg-white border-r overflow-y-auto">
          {data.map((book) => {
            const open = openBook === book.id;
            return (
              <div key={book.id} className="border-b">
                <button
                  onClick={() => setOpenBook(open ? null : book.id)}
                  className="w-full text-left px-4 py-3 flex items-center gap-2 hover:bg-gray-50"
                >
                  <span className="text-xl">{book.icon}</span>
                  <span className="flex-1 font-medium">{book.title}</span>
                  <span className="text-xs text-gray-400">{book.lessons.length} 课</span>
                  <span className="text-gray-400">{open ? "▾" : "▸"}</span>
                </button>
                {open && (
                  <ul className="bg-gray-50">
                    {book.lessons.map((lesson) => {
                      const isEditing =
                        edit?.bookId === book.id && edit?.lessonId === lesson.id;
                      return (
                        <li
                          key={lesson.id}
                          className={`px-4 py-2 flex items-center gap-2 border-t ${
                            isEditing ? "bg-blue-50" : ""
                          }`}
                        >
                          <span className="flex-1 text-sm">{lesson.title}</span>
                          <span className="text-xs text-gray-400">
                            {lesson.cards.length}
                          </span>
                          <button
                            onClick={() => startEdit(book.id, lesson)}
                            className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                          >
                            编辑
                          </button>
                          <button
                            onClick={() => del(book.id, lesson.id, lesson.title)}
                            disabled={busy}
                            className="text-xs px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                          >
                            删除
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </aside>

        <main className="flex-1 p-6">
          {!edit && (
            <div className="text-gray-500">
              从左边选择一课，点「编辑」开始修改。
              <div className="mt-4 text-sm">
                每行对应一张卡片（法文↔中文按行一一对应）。空行会被忽略。
              </div>
            </div>
          )}

          {edit && editingLesson && (
            <div className="max-w-5xl">
              <div className="flex items-center gap-3 mb-4">
                <label className="text-sm text-gray-500">标题</label>
                <input
                  value={edit.title}
                  onChange={(e) => setEdit({ ...edit, title: e.target.value })}
                  className="flex-1 border rounded px-3 py-2"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm text-gray-500">法文（每行一句）</label>
                    <span className="text-xs text-gray-400">{frontLineCount} 行</span>
                  </div>
                  <textarea
                    value={edit.front}
                    onChange={(e) => setEdit({ ...edit, front: e.target.value })}
                    className="w-full h-[60vh] border rounded p-3 font-mono text-sm leading-6"
                    spellCheck={false}
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm text-gray-500">中文（每行一句）</label>
                    <span
                      className={`text-xs ${
                        mismatch ? "text-red-600 font-semibold" : "text-gray-400"
                      }`}
                    >
                      {backLineCount} 行
                      {mismatch ? ` · 行数不匹配` : ""}
                    </span>
                  </div>
                  <textarea
                    value={edit.back}
                    onChange={(e) => setEdit({ ...edit, back: e.target.value })}
                    className="w-full h-[60vh] border rounded p-3 font-mono text-sm leading-6"
                    spellCheck={false}
                  />
                </div>
              </div>

              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={save}
                  disabled={busy}
                  className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {busy ? "保存中…" : "保存"}
                </button>
                <button
                  onClick={() => setEdit(null)}
                  disabled={busy}
                  className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
                >
                  取消
                </button>
                {mismatch && (
                  <span className="text-xs text-red-600">
                    提示：法文和中文行数不一致，保存时短的那一侧会补空字符串。
                  </span>
                )}
              </div>
            </div>
          )}

          {msg && (
            <div className="mt-4 text-sm text-gray-600 bg-white border rounded p-3">
              {msg}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
